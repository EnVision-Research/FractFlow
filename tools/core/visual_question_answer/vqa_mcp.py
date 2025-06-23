from typing import List, Dict, Optional, Any
import os
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
# Initialize FastMCP server
mcp = FastMCP("Visual_Question_Answering")

from PIL import Image
import base64
import io

def normalize_path(path: str) -> str:
    """
    Normalize a file path by expanding ~ to user's home directory
    and resolving relative paths.
    
    Args:
        path: The input path to normalize
        
    Returns:
        The normalized absolute path
    """
    # Expand ~ to user's home directory
    expanded_path = os.path.expanduser(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.abspath(expanded_path)
        
    return expanded_path

def encode_image(image: Image.Image, size: tuple[int, int] = (512, 512)) -> str:
    image.thumbnail(size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_image

def load_image(image_path: str, size_limit: tuple[int, int] = (512, 512)) -> tuple[str, dict]:
    """Load an image from the given path.
    
    Args:
        image_path: Path to the image file to load
        
    Returns:
        A tuple containing:
            - Base64 encoded string of the resized image (max 512x512) (this can be put in the image_url field of the user message)
            - Dictionary with metadata including original width and height
    """
    meta_info = {}
    image = Image.open(image_path)
    meta_info['width'], meta_info['height'] = image.size
    base64_image = encode_image(image, size_limit)
    return base64_image, meta_info

@mcp.tool()
async def Visual_Question_Answering(image_path: str, prompt: str) -> str:
    '''
    This tool uses Qwen-VL-Plus model to perform visual question answering or image analysis.
    The image is automatically resized to a maximum of 512x512 pixels before processing.
    
    Args:
        image_path (str): Full path to the image file to process. The path should be accessible
                          by the system and point to a valid image file (e.g., JPG, PNG).
        prompt (str): Text prompt describing what you want to know about the image. This can be:
                     - A direct question about the image content (e.g., "What objects are in this image?")
                     - A request for detailed description (e.g., "Describe this image in detail")
                     - A specific analytical instruction (e.g., "Count the number of people in this image")
    
    Returns:
        str: A detailed text response from the VLM model analyzing the image according to the prompt.
             The response format depends on the nature of the prompt.
    '''
    image_path = normalize_path(image_path)
    base64_image, meta_info = load_image(image_path, (512, 512))
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key=os.getenv('QWEN_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-max",  # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[{"role": "user","content": [
                {"type": "text","text": prompt},
                {"type": "image_url",
                "image_url": {"url": f'data:image/png;base64,{base64_image}'}}
                ]}]
    )
    return completion.choices[0].message.content

@mcp.tool()
async def Visual_Question_Answering_Multiple_Images(image_paths: List[str], prompt: str) -> str:
    '''
    This tool uses Qwen-VL-Plus model to perform visual question answering or image analysis on multiple images.
    All images are automatically resized to a maximum of 512x512 pixels before processing.
    
    Args:
        image_paths (List[str]): List of full paths to the image files to process. Each path should be accessible
                                by the system and point to a valid image file (e.g., JPG, PNG).
        prompt (str): Text prompt describing what you want to know about the images. This can be:
                     - A comparative question (e.g., "Compare these images and describe the differences")
                     - A collective analysis (e.g., "What common elements appear in all these images?")
                     - Individual analysis (e.g., "Describe each image separately")
                     - A specific analytical instruction (e.g., "Count objects across all images")
    
    Returns:
        str: A detailed text response from the VLM model analyzing all images according to the prompt.
             The response will consider all provided images in the context of the prompt.
    '''
    if not image_paths:
        return "Error: No image paths provided"
    
    # Normalize all paths and load images
    content_items = [{"type": "text", "text": prompt}]
    
    for i, image_path in enumerate(image_paths):
        try:
            normalized_path = normalize_path(image_path)
            base64_image, meta_info = load_image(normalized_path, (512, 512))
            
            # Add image to content with index for reference
            content_items.append({
                "type": "image_url",
                "image_url": {"url": f'data:image/png;base64,{base64_image}'}
            })
        except Exception as e:
            return f"Error loading image {i+1} ('{image_path}'): {str(e)}"
    
    client = OpenAI(
        api_key=os.getenv('QWEN_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[{"role": "user", "content": content_items}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error during VLM analysis: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 

