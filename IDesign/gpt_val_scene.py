import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import random
import requests
import base64
import json
import os
import time
random.seed(123)  # 设置随机种子为123


def GPT4V(image_path, prompt):
    url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"
    headers = { 
    "Content-Type": "application/json", 
    "Authorization": "cap3d 58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a" 
    }

    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    # Getting the base64 string
    base64_image = encode_image(image_path)
    system_message = 'You are a helpful assistant.'

    data = { 
      "messages": [ 
            { "role": "system", "content": system_message }, 
            { "role": "user", "content": [ 
            { 
            "type": "text", 
            "text": prompt 
            },
            { 
              "type": "image_url",
              "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
    }
          }
              ] } 
                ], 
    "temperature": 0.7,
    "max_tokens": 2000,
    "model": "gpt-4-turbo"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_content = response.json()
    message = response_content['choices'][0]['message']['content']

    return message

def get_image_files(directory):
    image_files = []
    # for i in range(0,30,3):
    for i in range(1,2):
        sub_path = str(i).zfill(2)
        now_path = os.path.join(directory, sub_path)
        all_png = os.listdir(now_path)
        for png in all_png:
            img_path = os.path.join(now_path, png)
            image_files.append(img_path)
        
    image_files = sorted(image_files, key=lambda x: (x.split('/')[3], x.split('/')[4]))

    # supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    # for root, dirs, files in os.walk(directory):
    #     for file in files:
    #         if os.path.splitext(file)[1].lower() in supported_extensions:
    #             image_files.append(os.path.join(root, file))
    return image_files


def GPT4V_evaluate_render(image_path1, image_path2):
    """评估 Blender 渲染的场景"""
    try:
        url = "https://gpt-api.hkust-gz.edu.cn/v1/chat/completions"
        headers = { 
            "Content-Type": "application/json", 
            "Authorization": "cap3d 58d0bacc761d4678855f9582819abcc77a4bacaa54984213905d9d546670638a" 
        }

        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        try:
            base64_image1 = encode_image(image_path1)
            base64_image2 = encode_image(image_path2)
            system_message = 'You are a helpful assistant.'

            example_json = """
            {
                "realism_and_3d_geometric_consistency": {
                    "grade": 8,
                    "comment": "The renders appear to have appropriate 3D geometry and lighting that is fairly consistent with real-world expectations. The proportions and perspective look realistic."
                },
                "functionality_and_activity_based_alignment": {
                    "grade": 7,
                    "comment": "The room includes a workspace, sleeping area, and living area as per the user preference. The L-shaped couch facing the bed partially meets the requirement for watching TV comfortably. However, there does not appear to be a TV depicted in the render, so it's not entirely clear if the functionality for TV watching is fully supported."
                },
                "layout_and_furniture": {
                    "grade": 7,
                    "comment": "The room has a bed that's not centered and with space at the foot, and a large desk with a chair. However, it's unclear if the height of the bed meets the user's preference, and the layout does not clearly show the full-length mirror in relation to the wardrobe, so its placement in accordance to user preferences is uncertain."
                },
                "color_scheme_and_material_choices": {
                    "grade": 9,
                    "comment": "The room adheres to a light color scheme with blue and white tones as preferred by the user, without a nautical feel. The bed and other furniture choices are aligned with the color scheme specified."
                },
                "overall_aesthetic_and_atmosphere": {
                    "grade": 8,
                    "comment": "The room's general aesthetic is bright, clean, and relatively minimalistic, which could align with the user's preference for a light color scheme and a modern look. The chandelier is present as opposed to bright, hospital-like lighting."
                }
            }
            """

            prompt = f"""Evaluate this rendered scene based on the following aspects:
            - Realism and 3D Geometric Consistency
            - Functionality and Activity-based Alignment
            - Layout and furniture  
            - Color Scheme and Material Choices
            - Overall Aesthetic and Atmosphere  
            
            Please provide grades (1-10) and brief comments for each aspect.
            Return your evaluation in the following JSON format:
            {example_json}
            
            Important: Please ensure your response is a valid JSON format that matches the example exactly.
            """

            data = { 
                "messages": [ 
                    {"role": "system", "content": system_message}, 
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image1}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image2}"}}    
                    ]} 
                ], 
                "temperature": 0.7,
                "max_tokens": 2000,
                "model": "gpt-4-turbo"
            }

            # 打印请求信息（不包含图片数据）
            print(f"\nSending request to API...")
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            print(f"\nAPI Response Status: {response.status_code}")
            
            response_content = response.json()
            print(f"\nAPI Response Content: {json.dumps(response_content, indent=2)}")
            import re

            def clean_json_string(content):
            # 使用正则表达式匹配JSON内容
                pattern = r'```(?:json)?\s*(\{[\s\S]*\})\s*```'
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
                # 如果没有markdown标记，直接返回内容
                return content.strip()
            
            if 'choices' in response_content and len(response_content['choices']) > 0:
                message = response_content['choices'][0]['message']['content']
                try:
                    # 如果返回的是带有 ```json 标记的内容，需要提取出 JSON 部分
                    # if message.startswith('```json'):
                    #     message = message.split('```json\n')[1].split('```')[0]
                    message = clean_json_string(message)
                    # 尝试解析返回的消息为JSON
                    evaluation = json.loads(message)
                    print(f"\n成功解析评估结果: {json.dumps(evaluation, indent=2, ensure_ascii=False)}")
                    return evaluation
                    
                except json.JSONDecodeError as e:
                    print(f"\nJSON解析错误: {str(e)}")
                    # 如果不是JSON格式，创建一个包含原始消息的结构
                    return {
                        "status": "error",
                        "message": message,
                        "error": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                error_msg = "API响应中没有找到有效的评估结果"
                print(f"\n{error_msg}")
                return {
                    "status": "error",
                    "message": error_msg,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
        except Exception as e:
            error_msg = f"评估过程发生错误: {str(e)}"
            print(f"\n{error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
    except Exception as e:
        print(f"\nError in GPT4V_evaluate_render: {str(e)}")
        return None

def main_work(render_path, path2):

    evaluations = {}

    image_path = render_path
    evaluation = GPT4V_evaluate_render(image_path, path2)
    if evaluation:
        evaluations[render_path] = evaluation

    # 保存评估结果
    try:
        with open('eval/scene_evaluation4.json', 'w', encoding='utf-8') as f:
            json.dump(evaluations, f, indent=2, ensure_ascii=False)
        print(f"评估结果已保存到: scene_evaluation.json")
    except Exception as e:
        print(f"保存评估结果时出错: {str(e)}")

if __name__ == '__main__':
    # 设置渲染输出路径
    render_output_path = '/remote-home/mingzesun/workspace/FractFlow/IDesign/render/4_render_camera_1.png'  # 从 Config 获取渲染输出路径
    path2 = '/remote-home/mingzesun/workspace/FractFlow/IDesign/render/4_render_camera_2.png'
    main_work(render_output_path, path2)

    

