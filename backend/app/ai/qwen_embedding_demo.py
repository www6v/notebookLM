import dashscope
import json
import os

# 多模态融合向量：将文本、图片、视频融合成一个向量
input_data = [
    {
        "text": "这是一段测试文本",
        "image": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png",
        "video": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250107/lbcemt/new+video.mp4"
    }
]

resp = dashscope.MultiModalEmbedding.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-vl-embedding",  # 或 tongyi-embedding-vision-plus
    input=input_data,
    # dimension=1024  # 可选
)

print(json.dumps(resp.output, indent=4))