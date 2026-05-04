"""Call MinerU ``do_parse`` directly so failures exit non-zero.

The stock ``mineru`` Click entrypoint catches exceptions inside ``parse_doc``,
logs them, and still exits 0, which makes the gateway think parsing succeeded
when no outputs were written.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path


def _truthy_env(name: str, default: str = "true") -> bool:
    raw = (os.environ.get(name) or default).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def main() -> int:
    if len(sys.argv) != 3:
        sys.stderr.write(
            "usage: python -m app.mineru_invoke PDF_PATH OUTPUT_DIR\n",
        )
        return 2
    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])

    from mineru.cli.common import do_parse, read_fn
    from mineru.utils.config_reader import get_device
    from mineru.utils.model_utils import get_vram

    backend = (os.environ.get("MINERU_GATEWAY_BACKEND") or "pipeline").strip()
    parse_method = (
        os.environ.get("MINERU_GATEWAY_PARSE_METHOD") or "auto"
    ).strip()
    lang = (os.environ.get("MINERU_GATEWAY_LANG") or "ch").strip()
    formula_enable = _truthy_env("MINERU_GATEWAY_FORMULA_ENABLE", "true")
    table_enable = _truthy_env("MINERU_GATEWAY_TABLE_ENABLE", "true")
    server_url = (os.environ.get("MINERU_GATEWAY_SERVER_URL") or "").strip() or None
    model_source = (
        os.environ.get("MINERU_MODEL_SOURCE") or "modelscope"
    ).strip()

    start_page_id = int(os.environ.get("MINERU_GATEWAY_START_PAGE", "0"))
    end_raw = (os.environ.get("MINERU_GATEWAY_END_PAGE") or "").strip()
    end_page_id = int(end_raw) if end_raw else None

    if not backend.endswith("-client"):
        if os.getenv("MINERU_DEVICE_MODE", None) is None:

            def _device_mode() -> str:
                override = os.environ.get("MINERU_GATEWAY_DEVICE")
                if override:
                    return override.strip()
                return get_device()

            device_mode = _device_mode()
            os.environ["MINERU_DEVICE_MODE"] = device_mode

            def _vram() -> int:
                if device_mode.startswith("cuda") or device_mode.startswith(
                    "npu",
                ):
                    return round(get_vram(device_mode))
                return 1

            if os.getenv("MINERU_VIRTUAL_VRAM_SIZE", None) is None:
                os.environ["MINERU_VIRTUAL_VRAM_SIZE"] = str(_vram())
        if os.getenv("MINERU_MODEL_SOURCE", None) is None:
            os.environ["MINERU_MODEL_SOURCE"] = model_source

    parse_started = time.perf_counter()
    do_parse(
        str(out_dir),
        [pdf_path.stem],
        [read_fn(pdf_path)],
        [lang],
        backend=backend,
        parse_method=parse_method,
        formula_enable=formula_enable,
        table_enable=table_enable,
        server_url=server_url,
        start_page_id=start_page_id,
        end_page_id=end_page_id,
    )
    parse_elapsed = time.perf_counter() - parse_started
    sys.stderr.write(
        f"mineru_invoke: do_parse took {parse_elapsed:.2f}s\n",
    )
    sys.stderr.flush()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1) from None
