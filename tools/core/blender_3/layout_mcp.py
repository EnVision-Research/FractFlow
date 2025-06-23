"""
Layout MCP Tool Provider - Space Planning and Layout

This module provides spatial layout and planning functionality for Blender scenes.
It focuses on space analysis, object placement planning, and layout validation.
"""

import sys
import time
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context
import json

# Import the BlenderPrimitive for unified Blender interaction
import sys
from pathlib import Path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from blender_primitive import blender_primitive
from typing import List

# Initialize FastMCP server
mcp = FastMCP("layout_manager")

@mcp.tool()
def analyze_scene_space() -> str:
    """
    分析当前场景的空间状况，返回原始数据
    
    Returns:
        str - 场景原始数据的自然语言描述
    """
    try:
        primitive = blender_primitive
        return primitive.get_raw_scene_data()
    except Exception as e:
        return f"✗ 场景分析时出错：{str(e)}"



@mcp.tool()
def validate_current_layout(ctx: Context) -> str:
    """
    验证当前场景中布局的可行性，返回原始数据让LLM分析
    
    Returns:
        str - 验证结果的自然语言报告
    """
    try:
        # 获取原始场景数据，让LLM自己分析
        scene_data = blender_primitive.get_raw_scene_data()
        
        if isinstance(scene_data, str) and "✗" in scene_data:
            return f"✗ 获取场景数据失败：{scene_data}"
        
        # 直接返回原始数据，让LLM进行分析
        return scene_data
        
    except Exception as e:
        return f"✗ 布局验证时出错：{str(e)}"

def _get_next_guide_number(item_type: str) -> int:
    """
    获取指定物品类型的下一个编号
    
    Args:
        item_type: 物品类型
        
    Returns:
        int - 下一个可用编号
    """
    try:
        # 使用原始数据接口获取引导线数据
        guides_data = blender_primitive.get_raw_guides_data()
        if isinstance(guides_data, str) and "✗" in guides_data:
            return 1  # 如果无法获取场景信息，从1开始
        
        # 从引导线数据中查找同类型引导线的最大编号
        max_number = 0
        
        if isinstance(guides_data, dict) and 'guides' in guides_data:
            for guide in guides_data['guides']:
                guide_name = guide.get('name', '')
                # 匹配类似 "LAYOUT_GUIDE_bed_1" 的模式
                if guide_name.startswith(f'LAYOUT_GUIDE_{item_type}_'):
                    try:
                        # 提取编号
                        number_part = guide_name.split(f'{item_type}_')[-1]
                        number = int(number_part)
                        max_number = max(max_number, number)
                    except (ValueError, IndexError):
                        continue
        
        return max_number + 1
        
    except Exception:
        return 1

@mcp.tool()
def create_layout_guide(
    guide_type: str,
    location: List[float],
    dimensions: List[float],
    semantic_id: str = "",
    design_intent: str = "",
    rotation: List[float] = [0, 0, 0],
    rotation_mode: str = "XYZ"
) -> str:
    """
    创建布局引导线
    
    Args:
        guide_type: 引导线类型 (如: bed, chair, table等)
        location: 位置 [x, y, z]
        dimensions: 尺寸 [width, depth, height]
        semantic_id: 语义ID (可选，如不提供会自动生成)
        design_intent: 设计意图描述 (可选)
        rotation: 旋转 [x, y, z] (弧度，可选，默认[0,0,0])
        rotation_mode: 旋转模式 (可选，默认"XYZ")
    
    Returns:
        str - 创建结果的自然语言描述
    """
    try:
        primitive = blender_primitive
        
        # 生成语义ID（如果未提供）
        if not semantic_id:
            next_number = _get_next_guide_number(guide_type)
            semantic_id = f"{guide_type}_{next_number}"
        
        # 生成对象名称
        guide_name = f"LAYOUT_GUIDE_{semantic_id}"
        
        # 构建扩展的元数据
        metadata = {
            "semantic_id": semantic_id,
            "item_type": guide_type,
            "design_intent": design_intent,
            "occupied": False,
            "occupied_by": "",
            # 新增旋转相关字段
            "rotation_mode": rotation_mode,
            "rotation_representation": "euler" if rotation_mode != "QUATERNION" else "quaternion",
            "rotation_semantic": design_intent,  # 语义化旋转描述
            "rotation_value": rotation
        }
        
        # 创建引导线（包含旋转）
        result = primitive.create_guide_cube(
            name=guide_name,
            location=location,
            dimensions=dimensions,
            metadata=metadata,
            rotation=rotation
        )
        
        return result
        
    except Exception as e:
        return f"✗ 创建引导线失败：{str(e)}"


@mcp.tool()
def clear_layout_guides(ctx: Context) -> str:
    """
    清除场景中所有的布局指导线
    
    Returns:
        str - 清除结果的自然语言报告
    """
    try:
        # 使用原始接口删除所有布局引导线
        result = blender_primitive.send_command("execute_code", {
            "code": """
import bpy
deleted_count = 0
deleted_names = []

for obj in list(bpy.data.objects):
    if obj.name.startswith("LAYOUT_GUIDE_"):
        deleted_names.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)
        deleted_count += 1

if deleted_count > 0:
    result = f"✓ 已删除 {deleted_count} 个布局引导线: {', '.join(deleted_names)}"
else:
    result = "场景中没有找到布局引导线"

print(result)
"""
        })
        
        return result
        
    except Exception as e:
        return f"✗ 清除布局引导线时出错：{str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio') 