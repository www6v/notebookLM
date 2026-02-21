"""Demo / reference for video understanding. 实际接口见 qwen3_vl_video.py."""

import asyncio

from app.ai.qwen3_vl_video import understand_video

# 示例：传入视频 URL，使用默认 prompt 与 fps
if __name__ == "__main__":
    text = asyncio.run(
        understand_video("https://example.com/video.mp4")
    )
    print(text)