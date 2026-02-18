import os
import dashscope
from dashscope import MultiModalConversation

# 设置 API Key（建议通过环境变量配置）
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')  # 或直接使用 'sk-xxx'

# 设置地域（根据你的服务区域选择）
# 北京地域（默认）：https://dashscope.aliyuncs.com/api/v1
# 新加坡地域：https://dashscope-intl.aliyuncs.com/api/v1  
# 弗吉尼亚地域：https://dashscope-us.aliyuncs.com/api/v1
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

def call_qwen3_vl():
    response = MultiModalConversation.call(
        model='qwen3-vl-plus',  # 模型名称
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": "https://example.com/image.jpg"},  # 图片URL
                    {"text": "请描述这张图片的内容"}
                ]
            }
        ]
    )
    print(response.output.choices[0].message.content[0]["text"])

if __name__ == '__main__':
    call_qwen3_vl()