import os
import base64
import json
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("doodle_understanding")



@mcp.tool()
async def analyze_doodle(
    image_path: str,
    description: str = "",
    api_key: str = ""
) -> str:
    """
    Analyze a child's doodle to understand their inner thoughts and feelings.
    
    This tool uses GPT-4o vision to understand what the child is thinking about their drawing.
    
    Args:
        image_path (str): Path to the doodle image file
        description (str): Optional description of what the child intended to draw
        api_key (str): API key for the HKUST-GZ GPT service (default: from environment variable HKUST_GPT_API_KEY)
    
    Returns:
        str: 2-3 sentences expressing the child's inner thoughts about their drawing
    """
    # 读取图片并转换为 Base64
    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    # 获取API密钥
    if not api_key.strip():
        api_key = os.getenv('HKUST_GPT_API_KEY')
        if not api_key:
            return "Error: API key not provided. Please set HKUST_GPT_API_KEY environment variable or provide api_key parameter"
    
    # 转换图片为base64
    base64_image = image_to_base64(image_path)
    
    # 根据是否有描述准备不同的提示词
    if description.strip():
        # 有描述的情况
        analysis_prompt = f"""请作为一位专业的儿童心理学家，通过观察这幅小朋友的画作，理解他们的内心世界。

小朋友说这幅画画的是：{description}

请用2-3句话，以小朋友的视角和语气，表达他们内心关于这幅画的真实想法和感受。比如他们为什么要画这个，这幅画对他们意味着什么，或者他们想通过这幅画表达什么情感。

请用温暖、童真的语言，像小朋友自己在说话一样。中文输出。"""
    else:
        # 只有图片的情况
        analysis_prompt = """请作为一位专业的儿童心理学家，通过观察这幅小朋友的画作，理解他们的内心世界。

请用2-3句话，以小朋友的视角和语气，表达他们内心关于这幅画的真实想法和感受。比如他们为什么要画这个，这幅画对他们意味着什么，或者他们想通过这幅画表达什么情感。

请用温暖、童真的语言，像小朋友自己在说话一样。中文输出。"""
    
    # API 请求
    url = "https://aigc-api.hkust-gz.edu.cn//v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "你是一位专业的儿童心理学家，擅长通过儿童的绘画作品理解他们的内心世界和情感状态。你能够用小朋友的视角和语言来表达他们的想法。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": analysis_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    api_response = requests.post(url, headers=headers, data=json.dumps(data))
    response = api_response.json()
    content = response['choices'][0]['message']['content']
    
    return content

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 
