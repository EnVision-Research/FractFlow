"""
Asset MCP - 资产管理模块

基于FractFlow分形智能架构的3D资产管理工具

核心设计理念:
1. 自然语言优先 - 提供原始数据，让LLM自主理解和分析
2. 简洁胜于复杂 - 避免硬编码的判断逻辑  
3. 工具描述即接口 - 通过自然语言描述暴露功能

主要功能:
- 从多个源下载3D资产
- 提供场景中对象和引导线的原始数据
- 协助资产的移动、旋转、缩放操作
- 支持资产与引导线的匹配和放置
"""

from mcp.server.fastmcp import FastMCP, Context
import time
import re

# 导入临时的BlenderPrimitive类
from blender_primitive import BlenderPrimitive

# 创建实例
blender_primitive = BlenderPrimitive()

# 创建MCP服务器
mcp = FastMCP("asset_mcp")

# ========== 内部辅助函数 ==========

# 删除了不再需要的辅助函数，直接使用blender-mcp的返回值

# ========== MCP工具函数 ==========

@mcp.tool()
def check_asset_sources_status(ctx: Context) -> str:
    """
    检查所有资产源的连接状态
    
    Returns:
        str - 各个资产源的状态报告
    """
    try:
        status_report = []
        
        # 检查PolyHaven状态
        polyhaven_status = get_polyhaven_status(ctx)
        status_report.append(f"PolyHaven: {polyhaven_status}")
        
        # 检查Sketchfab状态  
        sketchfab_status = get_sketchfab_status(ctx)
        status_report.append(f"Sketchfab: {sketchfab_status}")
        
        # 检查Hyper3D状态
        hyper3d_status = get_hyper3d_status(ctx)
        status_report.append(f"Hyper3D: {hyper3d_status}")
        
        return "✓ Asset Sources Status:\n" + "\n".join(status_report)
        
    except Exception as e:
        return f"✗ Error checking asset sources: {str(e)}"

@mcp.tool()
def search_asset(ctx: Context, item_type: str, style: str = "") -> str:
    """
    在多个资产源中搜索指定类型的资产
    
    Parameters:
        item_type: 资产类型，如"双人床"、"沙发"、"桌子"等
        style: 可选的风格描述，如"现代"、"古典"、"简约"等
    
    Returns:
        str - 搜索结果的详细报告，包含资产信息和下载标识符
    """
    try:
        search_results = []
        
        # 构建搜索查询
        search_query = f"{item_type} {style}".strip()
        
        # 搜索PolyHaven
        try:
            polyhaven_result = search_polyhaven_assets(ctx, "models", None)
            if "✓" in polyhaven_result:
                search_results.append(f"PolyHaven结果:\n{polyhaven_result}")
        except Exception as e:
            search_results.append(f"PolyHaven搜索失败: {str(e)}")
        
        # 搜索Sketchfab
        try:
            sketchfab_result = search_sketchfab_models(ctx, search_query, None, 20, True)
            if "✓" in sketchfab_result or "models found" in sketchfab_result:
                search_results.append(f"Sketchfab结果:\n{sketchfab_result}")
        except Exception as e:
            search_results.append(f"Sketchfab搜索失败: {str(e)}")
        
        if search_results:
            return "✓ 找到以下资产:\n\n" + "\n\n".join(search_results)
        else:
            return f"✗ 未找到匹配 '{search_query}' 的资产"
        
    except Exception as e:
        return f"✗ 搜索资产时出错: {str(e)}"

@mcp.tool()
def download_asset(
    ctx: Context, 
    source: str, 
    asset_identifier: str, 
    target_name: str = "",
    target_guide: str = "",
    target_scale: list = []
) -> str:
    """
    从指定源下载3D资产到Blender场景
    
    Parameters:
        source: 资产源名称 ("polyhaven", "sketchfab", "hyper3d", "file")
        asset_identifier: 资产的唯一标识符或描述
        target_name: 希望给资产设置的名称（可选）
        target_guide: 相关的引导线标识符（可选）
        target_scale: 希望设置的尺寸 [长,宽,高] 米（可选）
    
    Returns:
        str - 下载结果和导入对象的详细信息，包含原始数据供后续操作使用
    """
    try:
        # 1. 执行下载操作
        download_result = None
        if source.lower() == "polyhaven":
            download_result = _download_polyhaven_asset_raw(ctx, asset_identifier, "models", "1k")
        elif source.lower() == "sketchfab":
            download_result = _download_sketchfab_model_raw(ctx, asset_identifier)
        elif source.lower() == "hyper3d":
            download_result = _generate_hyper3d_model_raw(ctx, asset_identifier)
        elif source.lower() == "file":
            return f"建议使用 Blender 文件菜单导入 {asset_identifier}"
        else:
            return f"不支持的资产源: {source}。支持的源: polyhaven, sketchfab, hyper3d, file"
        
        # 2. 检查下载结果
        if not download_result:
            return f"下载失败：没有返回结果"
        
        if isinstance(download_result, dict) and download_result.get("error"):
            return f"下载失败: {download_result['error']}"
        
        # 3. 处理导入的对象
        imported_objects = []
        if isinstance(download_result, dict):
            imported_objects = download_result.get("imported_objects", [])
        
        if not imported_objects:
            # 尝试从字符串结果中提取对象名称
            if isinstance(download_result, str) and "imported successfully" in download_result.lower():
                # 简单的名称提取逻辑
                lines = download_result.split('\n')
                for line in lines:
                    if "imported" in line.lower() and "object" in line.lower():
                        # 尝试提取对象名称
                        import re
                        match = re.search(r'(\w+).*imported', line)
                        if match:
                            imported_objects = [match.group(1)]
                            break
        
        # 4. 构建结果报告
        result_info = {
            "source": source,
            "asset_identifier": asset_identifier,
            "download_result": download_result,
            "imported_objects": imported_objects,
            "imported_count": len(imported_objects)
        }
        
        # 5. 可选操作：重命名
        if target_name and imported_objects:
            if len(imported_objects) == 1:
                original_name = imported_objects[0]
                if original_name != target_name:
                    rename_result = blender_primitive.send_command("rename_object", {
                        "old_name": original_name,
                        "new_name": target_name
                    })
                    result_info["rename_result"] = rename_result
                    if "success" in str(rename_result).lower():
                        result_info["final_object_name"] = target_name
                    else:
                        result_info["final_object_name"] = original_name
                else:
                    result_info["final_object_name"] = target_name
            else:
                # 多个对象的情况，可以选择合并或保持原名
                result_info["final_object_name"] = imported_objects
        else:
            result_info["final_object_name"] = imported_objects
        
        # 6. 可选操作：缩放
        if target_scale and len(target_scale) >= 3:
            object_to_scale = result_info.get("final_object_name")
            if isinstance(object_to_scale, str):
                scale_result = scale_object(ctx, object_to_scale, target_scale)
                result_info["scale_result"] = scale_result
        
        # 7. 提供引导线信息（如果指定）
        if target_guide:
            guides_info = blender_primitive.get_raw_guides_data()
            result_info["available_guides"] = guides_info
            result_info["target_guide"] = target_guide
        
        # 8. 返回完整的原始数据，让LLM分析和决定后续操作
        return f"""✓ 资产下载完成

下载信息：
- 源: {source}
- 标识符: {asset_identifier}
- 导入对象: {imported_objects}
- 对象数量: {len(imported_objects)}

处理结果：
{result_info}

后续操作建议：
1. 如需移动对象，使用 move_object(object_name, [x, y, z])
2. 如需旋转对象，使用 rotate_object(object_name, [rx, ry, rz])
3. 如需缩放对象，使用 scale_object(object_name, [sx, sy, sz])
4. 如需查看场景信息，使用相应的查询工具

原始数据已提供，请根据需要进行后续操作。"""
        
    except Exception as e:
        return f"下载资产时出错: {str(e)}"

@mcp.tool()
def place_asset(
    ctx: Context,
    object_name: str,
    guide_identifier: str = "",
    apply_scale: list = None,
    apply_rotation: list = None
) -> str:
    """
    协助将资产放置到指定位置，提供引导线信息和操作建议
    
    Parameters:
        object_name: 要放置的对象名称
        guide_identifier: 引导线的标识符或描述（可选）
        apply_scale: 可选的缩放调整 [x, y, z] 或 [uniform_scale]
        apply_rotation: 可选的旋转调整 [x, y, z] (弧度)
    
    Returns:
        str - 包含对象信息、引导线数据和操作建议的完整报告
    """
    try:
        # 1. 检查对象是否存在，获取当前状态
        obj_data = blender_primitive.get_raw_object_data(object_name)
        if isinstance(obj_data, str) and "✗" in obj_data:
            return f"找不到对象 '{object_name}': {obj_data}"
        
        results = []
        
        # 2. 可选操作：应用缩放
        if apply_scale:
            scale_result = scale_object(ctx, object_name, apply_scale)
            results.append(f"缩放操作: {scale_result}")
        
        # 3. 可选操作：应用旋转
        if apply_rotation:
            rotate_result = rotate_object(ctx, object_name, apply_rotation)
            results.append(f"旋转操作: {rotate_result}")
        
        # 4. 获取所有引导线的原始数据
        guides_data = blender_primitive.get_raw_guides_data()
        
        # 5. 构建完整报告
        report = f"""对象放置协助报告

当前对象信息：
{obj_data}

所有可用引导线数据：
{guides_data}

"""
        
        if guide_identifier:
            report += f"""指定的引导线标识符: '{guide_identifier}'

放置建议：
1. 从上述引导线数据中找到与 '{guide_identifier}' 匹配的引导线
2. 提取该引导线的 location 坐标 [x, y, z]
3. 使用 move_object("{object_name}", [x, y, z]) 将对象移动到该位置

"""
        else:
            report += """放置建议：
1. 选择合适的引导线位置
2. 提取引导线的 location 坐标
3. 使用 move_object 将对象移动到目标位置

"""
        
        if results:
            report += f"已执行的操作：\n" + "\n".join(results) + "\n\n"
        
        report += """可用的后续操作：
- move_object(object_name, [x, y, z]) - 移动对象
- rotate_object(object_name, [rx, ry, rz]) - 旋转对象  
- scale_object(object_name, [sx, sy, sz]) - 缩放对象

所有原始数据已提供，请根据需要进行分析和操作。"""
        
        return report
        
    except Exception as e:
        return f"放置资产时出错: {str(e)}"


@mcp.tool()
def get_asset_info(ctx: Context, object_name: str) -> str:
    """
    获取资产的基本信息
    
    Parameters:
        object_name: 对象名称
    
    Returns:
        str - 资产信息的简单报告
    """
    try:
        # 使用新的自然语言接口获取对象信息
        obj_desc = blender_primitive.get_object_description(object_name)
        
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 直接返回自然语言描述
        return f"Asset Information:\n{obj_desc}"
        
    except Exception as e:
        return f"✗ Error getting asset info: {str(e)}"


@mcp.tool()
def fix_asset_ground(ctx: Context, object_name: str) -> str:
    """
    将资产固定到地面
    
    Parameters:
        object_name: 对象名称
    
    Returns:
        str - 操作结果的简单报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 从描述中提取当前位置
        import re
        pos_match = re.search(r'位于\(([^)]+)\)', obj_desc)
        if pos_match:
            coords = pos_match.group(1).split(', ')
            current_location = [float(c) for c in coords]
            
            # 设置新位置（Z坐标为0，放在地面上）
            ground_position = [current_location[0], current_location[1], 0.0]
            
            # 移动对象到地面
            move_result = blender_primitive.move_object(object_name, ground_position)
            
            if "✓" in move_result:
                return f"✓ Successfully fixed {object_name} to ground: {move_result}"
            else:
                return f"✗ Failed to fix {object_name} to ground: {move_result}"
        else:
            return f"✗ Could not extract position from object description"
        
    except Exception as e:
        return f"✗ Error fixing asset to ground: {str(e)}"


@mcp.tool()
def find_empty_guide_positions(ctx: Context, item_type: str = "") -> str:
    """
    查找空置的引导线位置
    
    Parameters:
        item_type: 可选的物品类型过滤
    
    Returns:
        str - 空置引导线位置的自然语言报告
    """
    try:
        # 使用新的自然语言接口查找空置引导线
        empty_guides_desc = blender_primitive.find_empty_guides(item_type)
        
        if "✗" in empty_guides_desc:
            return empty_guides_desc
        
        return f"Empty Guide Positions:\n{empty_guides_desc}"
        
    except Exception as e:
        return f"✗ Error finding empty guide positions: {str(e)}"


# combine_asset_parts 已移至内部函数 _combine_objects

# ========== 原始下载函数（内部使用） ==========

def _download_polyhaven_asset_raw(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "1k",
    file_format: str = None
) -> dict:
    """
    使用blender-mcp原生下载PolyHaven资产，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果，包含imported_objects列表
    """
    try:
        result = blender_primitive.send_command("download_polyhaven_asset", {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "resolution": resolution,
            "file_format": file_format
        })
        
        # blender-mcp可能返回字符串或dict，需要统一处理
        if isinstance(result, str):
            try:
                # 尝试解析JSON字符串
                import json
                parsed_result = json.loads(result)
                return parsed_result
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，检查是否是成功消息
                if "imported successfully" in result or "success" in result.lower():
                    # 从字符串中提取对象名称（简单解析）
                    if "imported_objects" in result:
                        # 尝试提取对象列表
                        import re
                        objects_match = re.search(r"imported_objects.*?(\[.*?\])", result)
                        if objects_match:
                            try:
                                objects_list = eval(objects_match.group(1))  # 简单评估
                                return {"success": True, "imported_objects": objects_list, "message": result}
                            except:
                                pass
                    # 如果无法提取，返回通用成功结果
                    return {"success": True, "imported_objects": [asset_id], "message": result}
                else:
                    return {"error": result, "success": False}
        elif isinstance(result, dict):
            return result
        else:
            return {"error": f"Unexpected result type: {type(result)}", "success": False}
        
    except Exception as e:
        return {"error": str(e), "success": False}

def _download_sketchfab_model_raw(ctx: Context, uid: str) -> dict:
    """
    使用blender-mcp原生下载Sketchfab模型，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果，包含imported_objects列表
    """
    try:
        result = blender_primitive.send_command("download_sketchfab_model", {
            "uid": uid
        })
        
        # blender-mcp可能返回字符串或dict，需要统一处理
        if isinstance(result, str):
            try:
                # 尝试解析JSON字符串
                import json
                parsed_result = json.loads(result)
                return parsed_result
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，检查是否是成功消息
                if "imported successfully" in result or "success" in result.lower():
                    # 从字符串中提取对象名称（简单解析）
                    if "imported_objects" in result:
                        # 尝试提取对象列表
                        import re
                        objects_match = re.search(r"imported_objects.*?(\[.*?\])", result)
                        if objects_match:
                            try:
                                objects_list = eval(objects_match.group(1))  # 简单评估
                                return {"success": True, "imported_objects": objects_list, "message": result}
                            except:
                                pass
                    # 如果无法提取，返回通用成功结果
                    return {"success": True, "imported_objects": [uid], "message": result}
                else:
                    return {"error": result, "success": False}
        elif isinstance(result, dict):
            return result
        else:
            return {"error": f"Unexpected result type: {type(result)}", "success": False}
        
    except Exception as e:
        return {"error": str(e), "success": False}

def _generate_hyper3d_model_raw(
    ctx: Context,
    text_prompt: str,
    bbox_condition: list = None
) -> dict:
    """
    使用blender-mcp原生生成Hyper3D模型，返回完整结果
    
    Returns:
        dict - blender-mcp的原始返回结果
    """
    try:
        result = blender_primitive.send_command("generate_hyper3d_model_via_text", {
            "text_prompt": text_prompt,
            "bbox_condition": bbox_condition
        })
        
        # 直接返回blender-mcp的原始结果
        return result
        
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool()
def get_guide_info(guide_identifier: str) -> str:
    """
    获取引导线的原始数据信息
    
    Args:
        guide_identifier: 引导线标识符
        
    Returns:
        str - 引导线原始数据的自然语言描述
    """
    try:
        # 直接获取所有引导线原始数据，让LLM分析匹配
        guides_data = blender_primitive.get_raw_guides_data()
        
        return f"✓ 查找引导线 '{guide_identifier}' 的信息：\n\n所有引导线原始数据：\n{guides_data}\n\n请从上述数据中找到匹配 '{guide_identifier}' 的引导线信息。"
        
    except Exception as e:
        return f"✗ 获取引导线信息时出错：{str(e)}"



@mcp.tool()
def list_available_guides() -> str:
    """
    列出所有可用引导线的原始数据
    
    Returns:
        str - 所有引导线原始数据的自然语言描述
    """
    try:
        primitive = BlenderPrimitive()
        return primitive.get_raw_guides_data()
    except Exception as e:
        return f"✗ 列出引导线时出错：{str(e)}"

# ========== 从 blender-mcp 导入的资产功能 ==========

# 添加必要的导入
import json
import os
import base64
from pathlib import Path
from urllib.parse import urlparse

def _process_bbox(bbox_condition):
    """处理bbox条件"""
    if bbox_condition is None:
        return None
    return bbox_condition

# ========== PolyHaven 资产功能 ==========

@mcp.tool()
def get_polyhaven_categories(ctx: Context, asset_type: str = "hdris") -> str:
    """
    获取PolyHaven资产分类列表
    
    Parameters:
    - asset_type: 资产类型 (hdris, textures, models, all)
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_polyhaven_categories", {"asset_type": asset_type})
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error getting PolyHaven categories: {str(e)}"

@mcp.tool()
def search_polyhaven_assets(
    ctx: Context,
    asset_type: str = "all",
    categories: str = None
) -> str:
    """
    在PolyHaven搜索资产
    
    Parameters:
    - asset_type: 资产类型 (hdris, textures, models, all)
    - categories: 可选的分类过滤，用逗号分隔
    
    Returns: 匹配资产的格式化列表
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("search_polyhaven_assets", {
            "asset_type": asset_type,
            "categories": categories
        })
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error searching PolyHaven assets: {str(e)}"

# download_polyhaven_asset 已移至内部函数 _download_polyhaven_asset_raw

@mcp.tool()
def get_polyhaven_status(ctx: Context) -> str:
    """
    检查PolyHaven集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_polyhaven_status")
        return str(result)
    except Exception as e:
        return f"Error checking PolyHaven status: {str(e)}"

# ========== Sketchfab 模型功能 ==========

@mcp.tool()
def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: str = None,
    count: int = 20,
    downloadable: bool = True
) -> str:
    """
    在Sketchfab搜索模型
    
    Parameters:
    - query: 搜索文本
    - categories: 可选分类过滤，用逗号分隔
    - count: 最大结果数量 (默认20)
    - downloadable: 是否只包含可下载模型 (默认True)
    
    Returns: 匹配模型的格式化列表
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("search_sketchfab_models", {
            "query": query,
            "categories": categories,
            "count": count,
            "downloadable": downloadable
        })
        
        if "error" in str(result):
            return f"Error: {result}"
        
        return result
    except Exception as e:
        return f"Error searching Sketchfab models: {str(e)}"

# download_sketchfab_model 已移至内部函数 _download_sketchfab_model_raw

@mcp.tool()
def get_sketchfab_status(ctx: Context) -> str:
    """
    检查Sketchfab集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_sketchfab_status")
        return str(result)
    except Exception as e:
        return f"Error checking Sketchfab status: {str(e)}"

# ========== Hyper3D AI生成功能 ==========

# generate_hyper3d_model_via_text 已移至内部函数 _generate_hyper3d_model_raw

@mcp.tool()
def get_hyper3d_status(ctx: Context) -> str:
    """
    检查Hyper3D集成状态
    """
    try:
        primitive = BlenderPrimitive()
        result = primitive.send_command("get_hyper3d_status")
        return str(result)
    except Exception as e:
        return f"Error checking Hyper3D status: {str(e)}"

# ========== 独立的变换工具 ==========

@mcp.tool()
def scale_object(ctx: Context, object_name: str, scale_factors: list) -> str:
    """
    将对象缩放到指定的绝对尺寸
    
    Parameters:
        object_name: 要缩放的对象名称
        scale_factors: 目标绝对尺寸 [x, y, z] (米) 或 [uniform_size] (等比缩放到该尺寸)
    
    Returns:
        str - 缩放结果报告，包含尺寸变化信息
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 处理等比缩放
        if len(scale_factors) == 1:
            scale_factors = [scale_factors[0], scale_factors[0], scale_factors[0]]
        elif len(scale_factors) != 3:
            return f"✗ scale_factors must be [x, y, z] or [uniform_scale]"
        
        # 执行缩放
        result = blender_primitive.scale_object(object_name, scale_factors)
        
        if "✗" in result:
            return f"✗ Failed to scale {object_name}: {result}"
        
        return f"✓ Successfully scaled {object_name} to [{scale_factors[0]:.2f}, {scale_factors[1]:.2f}, {scale_factors[2]:.2f}]"
        
    except Exception as e:
        return f"✗ Error scaling object: {str(e)}"


@mcp.tool()
def move_object(ctx: Context, object_name: str, position: list) -> str:
    """
    移动对象到指定位置
    
    Parameters:
        object_name: 要移动的对象名称
        position: 目标位置 [x, y, z]
    
    Returns:
        str - 移动结果报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        if len(position) != 3:
            return f"✗ position must be [x, y, z]"
        
        # 执行移动
        result = blender_primitive.move_object(object_name, position)
        
        if "✗" in result:
            return f"✗ Failed to move {object_name}: {result}"
        
        return f"✓ Successfully moved {object_name} to [{position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f}]"
        
    except Exception as e:
        return f"✗ Error moving object: {str(e)}"


@mcp.tool()
def rotate_object(ctx: Context, object_name: str, rotation: list, rotation_mode: str = "XYZ") -> str:
    """
    旋转对象到指定角度（支持多种旋转模式）
    
    Parameters:
        object_name: 要旋转的对象名称
        rotation: 目标旋转值列表
        rotation_mode: 旋转模式 ("XYZ", "QUATERNION", "AXIS_ANGLE"等)
    
    Returns:
        str - 旋转结果报告
    """
    try:
        # 检查对象是否存在
        obj_desc = blender_primitive.get_object_description(object_name)
        if "✗" in obj_desc:
            return f"✗ Object '{object_name}' not found in scene"
        
        # 验证旋转值长度
        expected_length = 4 if rotation_mode in ["QUATERNION", "AXIS_ANGLE"] else 3
        if len(rotation) != expected_length:
            return f"✗ {rotation_mode} mode requires {expected_length} values, got {len(rotation)}"
        
        # 使用统一旋转接口
        result = blender_primitive.rotate_object_unified(object_name, rotation, rotation_mode, "XYZ")
        
        if isinstance(result, str) and "✗" in result:
            return f"✗ Failed to rotate {object_name}: {result}"
        
        # 解析JSON结果
        import json
        try:
            if isinstance(result, str):
                result_data = json.loads(result.strip().split('\n')[-1])
            else:
                result_data = result
                
            if result_data.get('success'):
                # 转换为度数显示（仅对欧拉角）
                final_rotation = result_data.get('final_rotation', rotation)
                if len(final_rotation) == 3:
                    degrees = [r * 180 / 3.14159 for r in final_rotation[:3]]
                    return f"✓ Successfully rotated {object_name} to [{degrees[0]:.1f}°, {degrees[1]:.1f}°, {degrees[2]:.1f}°] (mode: {result_data.get('target_mode', rotation_mode)})"
                else:
                    return f"✓ Successfully rotated {object_name} using {result_data.get('target_mode', rotation_mode)} mode"
            else:
                return f"✗ Rotation failed: {result_data.get('error', 'Unknown error')}"
                
        except json.JSONDecodeError:
            return f"✓ Rotation command executed (result: {result})"
        
    except Exception as e:
        return f"✗ Error rotating object: {str(e)}"


@mcp.tool()
def match_asset_rotation_to_guide(ctx: Context, asset_name: str, guide_name: str) -> str:
    """
    将资产的旋转匹配到导引线的旋转
    
    Parameters:
        asset_name: 资产对象名称
        guide_name: 导引线对象名称
    
    Returns:
        str - 匹配结果报告
    """
    try:
        # 使用Blender MCP直接执行旋转匹配
        script = f"""
import bpy
import sys
import json

# 导入RotationManager
sys.path.append('/Users/yingcongchen/Documents/code/AI原生开发/EnvisionCore-evolve/FractFlow/tools/core/blender_3')
from rotation_manager import rotation_manager

# 获取对象
asset_obj = bpy.data.objects.get("{asset_name}")
guide_obj = bpy.data.objects.get("{guide_name}")

if not asset_obj:
    result = {{"success": False, "error": "Asset object '{asset_name}' not found"}}
elif not guide_obj:
    result = {{"success": False, "error": "Guide object '{guide_name}' not found"}}
else:
    # 执行旋转匹配
    result = rotation_manager.match_rotation_to_guide(asset_obj, guide_obj)

print(json.dumps(result))
"""
        
        match_result = blender_primitive.send_command("execute_code", {"code": script})
        
        # 解析结果
        import json
        try:
            # 从Blender MCP结果中提取JSON
            if isinstance(match_result, dict) and 'result' in match_result:
                result_str = match_result['result']
                # 提取JSON部分
                if isinstance(result_str, str):
                    lines = result_str.strip().split('\n')
                    for line in lines:
                        if line.strip().startswith('{') and line.strip().endswith('}'):
                            result_data = json.loads(line.strip())
                            break
                    else:
                        raise json.JSONDecodeError("No valid JSON found", result_str, 0)
                else:
                    result_data = result_str
            else:
                result_data = match_result
                
            if result_data.get('success'):
                guide_rotation = result_data.get('guide_rotation', [])
                guide_mode = result_data.get('guide_mode', 'Unknown')
                target_mode = result_data.get('target_mode', 'Unknown')
                
                return f"""✓ Successfully matched {asset_name} rotation to {guide_name}:
   - Guide rotation: {[round(x, 3) for x in guide_rotation]} ({guide_mode})
   - Asset converted to: {target_mode} mode
   - Rotation alignment: Complete"""
            else:
                return f"✗ Rotation matching failed: {result_data.get('error', 'Unknown error')}"
                
        except json.JSONDecodeError:
            return f"✗ Failed to parse rotation matching result: {match_result}"
        
    except Exception as e:
        return f"✗ Error matching rotations: {str(e)}"


@mcp.tool()
def standardize_object_rotation_mode(ctx: Context, object_name: str, target_mode: str = "XYZ") -> str:
    """
    标准化对象的旋转模式
    
    Parameters:
        object_name: 要标准化的对象名称
        target_mode: 目标旋转模式 (默认"XYZ")
    
    Returns:
        str - 标准化结果报告
    """
    try:
        # 使用Blender MCP执行标准化
        script = f"""
import bpy
import sys
import json

# 导入RotationManager
sys.path.append('/Users/yingcongchen/Documents/code/AI原生开发/EnvisionCore-evolve/FractFlow/tools/core/blender_3')
from rotation_manager import rotation_manager

# 获取对象
obj = bpy.data.objects.get("{object_name}")

if not obj:
    result = {{"success": False, "error": "Object '{object_name}' not found"}}
else:
    # 执行标准化
    result = rotation_manager.standardize_rotation_mode(obj, "{target_mode}")

print(json.dumps(result))
"""
        
        std_result = blender_primitive.send_command("execute_code", {"code": script})
        
        # 解析结果
        import json
        try:
            if isinstance(std_result, str):
                result_data = json.loads(std_result.strip().split('\n')[-1])
            else:
                result_data = std_result
                
            if result_data.get('success'):
                message = result_data.get('message', 'Standardization completed')
                return f"✓ {object_name}: {message}"
            else:
                return f"✗ Standardization failed: {result_data.get('error', 'Unknown error')}"
                
        except json.JSONDecodeError:
            return f"✗ Failed to parse standardization result: {std_result}"
        
    except Exception as e:
        return f"✗ Error standardizing rotation mode: {str(e)}"


@mcp.tool()
def debug_scene_objects(ctx: Context) -> str:
    """
    调试工具：检查当前场景中的所有对象
    
    Returns:
        str - 场景中所有对象的详细信息
    """
    try:
        # 获取原始场景数据
        scene_data = blender_primitive.get_raw_scene_data()
        
        if isinstance(scene_data, dict):
            objects_info = []
            if 'objects' in scene_data:
                for obj in scene_data['objects']:
                    obj_info = f"- {obj.get('name', 'Unknown')}: 位置{obj.get('location', 'N/A')}, 尺寸{obj.get('dimensions', 'N/A')}"
                    objects_info.append(obj_info)
            
            total_objects = len(scene_data.get('objects', []))
            
            return f"""✓ 场景调试信息:
总对象数: {total_objects}

对象列表:
{chr(10).join(objects_info) if objects_info else '无对象'}

原始数据:
{scene_data}
"""
        else:
            return f"✗ 无法获取场景数据: {scene_data}"
        
    except Exception as e:
        return f"✗ 调试场景时出错: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio') 