#This is an example that uses the websockets api to know when a prompt execution is done
#Once the prompt execution is done it downloads the images using the /history endpoint

import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import os
import base64
import io
from typing import Dict, Any, Optional
from PIL import Image
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("comfyui")

server_address = "127.0.0.1:8188"
# Set the ComfyUI path
comfyui_path = "/Users/yingcongchen/Documents/code/ComfyUI"

def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt, client_id):
    prompt_id = queue_prompt(prompt, client_id)['prompt_id']
    output_images = {}
    output_image_paths = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            # If you want to be able to decode the binary stream for latent previews, here is how you can do it:
            # bytesIO = BytesIO(out[8:])
            # preview_image = Image.open(bytesIO) # This is your preview in PIL image format, store it in a global
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        image_paths = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
                
                # Construct the full path to the saved image
                if image['type'] == 'output':
                    # For output images, the path is in the ComfyUI/output directory
                    image_path = os.path.join(comfyui_path, "output")
                    if image['subfolder']:
                        image_path = os.path.join(image_path, image['subfolder'])
                    image_path = os.path.join(image_path, image['filename'])
                    image_paths.append(image_path)
                    
        output_images[node_id] = images_output
        output_image_paths[node_id] = image_paths

    return output_images, output_image_paths

def encode_image(image_data, size=(512, 512)):
    image = Image.open(io.BytesIO(image_data))
    image.thumbnail(size)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_image

@mcp.tool()
async def generate_image_with_comfyui(
    positive_prompt: str = "masterpiece best quality",
    negative_prompt: str = "bad hands",
    width: int = 512,
    height: int = 512,
    seed: int = 0,
    steps: int = 1,
    cfg: float = 1,
    checkpoint: str = "SDXL-TURBO/sd_xl_turbo_1.0_fp16.safetensors"
) -> str:
    """
    Generate an image using ComfyUI with the specified parameters
    
    Args:
        positive_prompt: Positive text prompt for image generation （It should be English）
        negative_prompt: Negative text prompt for image generation （It should be English）
        width: Image width (default: 512)
        height: Image height (default: 512)
        seed: Seed for the generation (default: 0)
        steps: Number of steps for sampling (default: 1)
        cfg: CFG scale for guidance (default: 1)
        checkpoint: Model checkpoint to use (default: "SDXL-TURBO/sd_xl_turbo_1.0_fp16.safetensors")
        
    Returns:
        Image file path as a string
    """
    # Create a workflow template
    prompt = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": cfg,
                "denoise": 1,
                "latent_image": [
                    "5",
                    0
                ],
                "model": [
                    "4",
                    0
                ],
                "negative": [
                    "7",
                    0
                ],
                "positive": [
                    "6",
                    0
                ],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": seed,
                "steps": steps
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": height,
                "width": width
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": [
                    "4",
                    1
                ],
                "text": positive_prompt
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": [
                    "4",
                    1
                ],
                "text": negative_prompt
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": [
                    "3",
                    0
                ],
                "vae": [
                    "4",
                    2
                ]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": [
                    "8",
                    0
                ]
            }
        }
    }
    
    # Generate a unique client ID
    client_id = str(uuid.uuid4())
    
    # Connect to ComfyUI websocket
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    
    # Get the generated images
    try:
        images, image_paths = get_images(ws, prompt, client_id)
        
        # Find the first image path and return it directly
        for node_id in image_paths:
            if image_paths[node_id] and len(image_paths[node_id]) > 0:
                # Return just the image path string
                return image_paths[node_id][0]
                    
        return "No image generated"
    
    finally:
        ws.close()

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

