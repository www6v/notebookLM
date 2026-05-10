"""DeerFlow HTTP client for Deep Research (production-grade).

Integrates with bytedance/deer-flow (https://github.com/bytedance/deer-flow)
LangGraph + Gateway API: create thread, run research task, consume SSE stream.
"""

import json
import logging
import re
import httpx

from notebooklm_shared.config import settings

logger = logging.getLogger(__name__)

DEEP_RESEARCH_SYSTEM_HINT = (
    "在报告正文末尾单独一行写出统计信息，格式为："
    "来源总数：N，热门来源：M。"
    "（N和M为数字）"
)


async def create_thread(base_url: str) -> str:
    """Create a DeerFlow LangGraph thread. Returns thread_id."""
    url = f"{base_url.rstrip('/')}/api/langgraph/threads"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json={})
        resp.raise_for_status()
        data = resp.json()
        thread_id = data.get("thread_id")
        if not thread_id:
            raise ValueError("DeerFlow create thread: missing thread_id")
        return thread_id


def _research_user_message(query: str) -> str:
    """Build the user message for a deep research task."""
    return (
        f"请对以下主题进行深度研究（使用网络搜索与多来源综合），并生成一份结构化报告。"
        f"报告需包含：研究结论、关键发现、可靠来源。\n\n"
        f"主题：{query}\n\n"
        f"{DEEP_RESEARCH_SYSTEM_HINT}"
    )


def _parse_source_counts_from_content(text: str) -> tuple[int, int]:
    """Parse source_count and popular_count from report content if present."""
    # 来源总数：38，热门来源：20
    m = re.search(r"来源总数[：:]\s*(\d+)[，,]\s*热门来源[：:]\s*(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    # SOURCES: 38, POPULAR: 20
    m = re.search(r"SOURCES?[：:]\s*(\d+)[，,]\s*POPULAR[：:]\s*(\d+)", text, re.I)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _strip_trailing_source_line(content: str) -> str:
    """Remove the trailing '来源总数：N，热门来源：M' line for display."""
    return re.sub(
        r"\n?\s*来源总数[：:]\s*\d+[，,]\s*热门来源[：:]\s*\d+\.?\s*$",
        "",
        content,
        flags=re.MULTILINE,
    ).strip()


def _message_content_to_str(content: object) -> str:
    """Normalize LangChain/LangGraph message content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and "text" in block:
                    parts.append(str(block["text"]))
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return ""


def _latest_ai_text_from_values_state(state: dict) -> str:
    """Take the last AI message from a LangGraph ``values`` snapshot."""
    msgs = state.get("messages")
    if not isinstance(msgs, list):
        return ""
    for m in reversed(msgs):
        if not isinstance(m, dict):
            continue
        typ = m.get("type")
        if typ in ("ai", "AIMessage"):
            body = _message_content_to_str(m.get("content"))
            if body.strip():
                return body
    return ""


def _ai_fragment_from_messages_event_payload(obj: object) -> str | None:
    """Parse ``messages`` / ``messages-tuple`` SSE payloads (chunk or dict)."""
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        msg = obj[0]
        typ = str(msg.get("type") or "")
        if "AIMessageChunk" in typ or typ == "ai":
            c = msg.get("content")
            if isinstance(c, str) and c:
                return c
    if isinstance(obj, dict):
        typ = obj.get("type")
        if typ == "ai":
            c = obj.get("content")
            if isinstance(c, str) and c:
                return c
            if isinstance(c, list):
                text = _message_content_to_str(c)
                return text or None
    return None


def _apply_sse_data_line(
    event: str | None,
    data_payload: str,
    latest_values_ai: list[str],
    message_chunks: list[str],
) -> None:
    """Apply one completed SSE event's joined ``data`` lines."""
    if not event or not data_payload:
        return
    try:
        obj = json.loads(data_payload)
    except (json.JSONDecodeError, TypeError):
        return
    if event == "values" and isinstance(obj, dict):
        text = _latest_ai_text_from_values_state(obj)
        if text:
            latest_values_ai[0] = text
        return
    # LangGraph 0.7+: ``messages/partial``, ``messages/metadata``, etc.
    if event.startswith("messages") or event == "messages-tuple":
        frag = _ai_fragment_from_messages_event_payload(obj)
        if frag:
            message_chunks.append(frag)


async def _consume_langgraph_sse(response: httpx.Response) -> str:
    """Read SSE from LangGraph gateway; prefer final ``values`` AI message."""
    latest_values_ai: list[str] = [""]
    message_chunks: list[str] = []
    pending_event: str | None = None
    pending_data: list[str] = []

    def flush_event() -> None:
        if pending_event and pending_data:
            payload = "\n".join(pending_data)
            _apply_sse_data_line(
                pending_event,
                payload,
                latest_values_ai,
                message_chunks,
            )
        pending_data.clear()

    async for raw in response.aiter_lines():
        line = raw.rstrip("\n\r")
        if not line:
            flush_event()
            pending_event = None
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            flush_event()
            pending_event = line[6:].strip()
            pending_data = []
            continue
        if line.startswith("data:"):
            pending_data.append(line[5:].lstrip())

    flush_event()

    full = (latest_values_ai[0] or "").strip()
    if full:
        return full
    return "".join(message_chunks)


async def run_research_and_collect(
    base_url: str,
    thread_id: str,
    query: str,
    timeout_seconds: int,
) -> tuple[str, int, int]:
    """Run a research task on DeerFlow and collect the final report content.

    Returns:
        (content, source_count, popular_count)
    """
    root = base_url.rstrip("/")
    runs_url = f"{root}/api/langgraph/threads/{thread_id}/runs"
    graph_id = settings.deer_flow_assistant_id
    # DeerFlow gateway: POST /runs returns JSON (run_id); stream is a separate
    # GET on /runs/{run_id}/stream (not the POST body as SSE).
    # Middleware reads thread_id from Runtime.context.
    payload = {
        "assistant_id": graph_id,
        "input": {
            "messages": [
                {"role": "user", "content": _research_user_message(query)},
            ],
        },
        "stream_mode": ["values", "messages", "messages-tuple"],
        "context": {"thread_id": thread_id},
    }

    timeout = httpx.Timeout(timeout_seconds, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        start = await client.post(runs_url, json=payload)
        start.raise_for_status()
        run_body = start.json()
        run_id = run_body.get("run_id")
        if not run_id:
            raise ValueError("DeerFlow start run: missing run_id in response")

        stream_url = (
            f"{root}/api/langgraph/threads/{thread_id}/runs/{run_id}/stream"
        )
        async with client.stream(
            "GET",
            stream_url,
            headers={"Accept": "text/event-stream"},
        ) as stream_resp:
            stream_resp.raise_for_status()
            full_content = await _consume_langgraph_sse(stream_resp)

    source_count, popular_count = _parse_source_counts_from_content(
        full_content
    )
    display_content = _strip_trailing_source_line(full_content)
    if not display_content and full_content:
        display_content = full_content
    return display_content, source_count, popular_count


async def run_deep_research(
    query: str,
    base_url: str | None = None,
    timeout_seconds: int | None = None,
) -> tuple[str, int, int]:
    """Create thread, run research; return content and source counts.

    Raises:
        httpx.HTTPStatusError: on DeerFlow API errors
        ValueError: on invalid response
    """
    base_url = base_url or settings.deer_flow_base_url
    timeout_seconds = timeout_seconds or settings.deer_flow_timeout_seconds

    thread_id = await create_thread(base_url)
    logger.info("DeerFlow thread created: %s", thread_id)

    content, source_count, popular_count = await run_research_and_collect(
        base_url, thread_id, query, timeout_seconds
    )
    return content, source_count, popular_count
