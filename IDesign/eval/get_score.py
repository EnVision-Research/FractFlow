import os
import json
import numpy as np
from glob import glob

def calculate_average_scores():
    # 获取当前目录下所有的scene_evaluation*.json文件
    json_files = glob("scene_evaluation*.json")
    
    if not json_files:
        print("当前目录下没有找到scene_evaluation*.json文件")
        return
    
    print(f"找到 {len(json_files)} 个评估文件")
    
    # 存储所有评分类别的分数
    categories = [
        "realism_and_3d_geometric_consistency",
        "functionality_and_activity_based_alignment",
        "layout_and_furniture",
        "color_scheme_and_material_choices",
        "overall_aesthetic_and_atmosphere"
    ]
    
    all_scores = {category: [] for category in categories}
    
    # 处理每个JSON文件
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_scores = []
            # 遍历每个图像路径
            for image_path, evaluations in data.items():
                # 收集此图像的所有分数
                for category in categories:
                    if category in evaluations:
                        score = evaluations[category]["grade"]
                        all_scores[category].append(score)
                        file_scores.append((category, score))
            
            # 打印此文件的分数
            print(f"\n文件 {file_path} 的评分:")
            for category, score in file_scores:
                print(f"  {category}: {score}")
                
        except json.JSONDecodeError:
            print(f"文件 {file_path} 不是有效的JSON")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 计算每个类别的平均分
    print("\n各类别平均分数:")
    category_averages = []
    for category in categories:
        scores = all_scores[category]
        if scores:
            avg = np.mean(scores)
            category_averages.append(avg)
            print(f"{category}: {avg:.2f}")
        else:
            print(f"{category}: 无数据")
    
    # 计算总体平均分
    if category_averages:
        overall_avg = np.mean(category_averages)
        print(f"\n总体平均分: {overall_avg:.2f}")
    else:
        print("没有找到有效的分数数据")

if __name__ == "__main__":
    calculate_average_scores()