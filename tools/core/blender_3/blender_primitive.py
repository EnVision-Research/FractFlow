"""
BlenderPrimitive - 原始数据接口
提供Blender场景的原始数值数据，不做任何推断或解释
让LLM自己理解数值的含义
"""

from typing import List, Dict, Any, Optional
import json
import sys
import os

# 导入Blender连接
try:
    # 添加blender-mcp到路径
    blender_mcp_src = os.path.join(os.path.dirname(__file__), "blender-mcp", "src")
    if os.path.exists(blender_mcp_src):
        sys.path.insert(0, blender_mcp_src)
    
    from blender_mcp.server import get_blender_connection
except ImportError as e:
    # 只保留错误处理的print
    print(f"Warning: Could not import blender-mcp modules: {e}")
    get_blender_connection = None


class BlenderPrimitive:
    """
    Blender原始数据接口 - 专注于提供原始数据，让LLM自主理解
    
    设计原则：
    1. 提供原始数据，避免预处理和"翻译"
    2. 让LLM自己分析和理解数据含义
    3. 避免硬编码的语义判断
    4. 保持接口简洁，功能专一
    """
    
    def __init__(self):
        self.blender = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """初始化Blender连接"""
        if get_blender_connection is not None:
            try:
                self.blender = get_blender_connection()
            except Exception as e:
                # 只保留错误处理的print
                print(f"警告：无法连接到Blender MCP服务器: {e}")
                self.blender = None
    
    def send_command(self, tool_name, arguments=None):
        """向Blender发送命令"""
        if self.blender is None:
            return "✗ Blender连接不可用"
        
        try:
            if arguments is None:
                arguments = {}
            result = self.blender.send_command(tool_name, arguments)
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            return f"✗ 执行命令失败: {e}"
    
    # ========== 原始数据获取接口 ==========
    
    def get_raw_scene_data(self):
        """获取场景中所有对象的原始数据"""
        script = """
import bpy
import json

scene_data = {
    'total_count': len(bpy.data.objects),
    'objects': [],
    'boundaries': {'min': [0, 0, 0], 'max': [0, 0, 0]}
}

# 收集所有对象信息
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj_data = {
            'name': obj.name,
            'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
            'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
            'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
            'type': obj.type
        }
        
        # 获取元数据
        if 'guide_metadata' in obj:
            try:
                obj_data['metadata'] = json.loads(obj['guide_metadata'])
            except:
                obj_data['metadata'] = obj['guide_metadata']
        else:
            obj_data['metadata'] = None
            
        scene_data['objects'].append(obj_data)

# 计算场景边界
if scene_data['objects']:
    all_locations = [obj['location'] for obj in scene_data['objects']]
    min_coords = [min(loc[i] for loc in all_locations) for i in range(3)]
    max_coords = [max(loc[i] for loc in all_locations) for i in range(3)]
    scene_data['boundaries'] = {'min': min_coords, 'max': max_coords}

print(json.dumps(scene_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        # 直接返回原始数据，不添加格式化输出
        if result.startswith("✗"):
            return result
        
        try:
            import json
            scene_data = json.loads(result.split('\n')[-2])
            return scene_data
        except:
            return result
    
    def get_raw_object_data(self, name):
        """获取单个对象的原始数据"""
        script = f"""
import bpy
import json

obj = bpy.data.objects.get("{name}")
if not obj:
    print("✗ 未找到对象")
elif obj.type != 'MESH':
    print("✗ 不是网格对象")
else:
    obj_data = {{
        'name': obj.name,
        'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
        'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
        'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
        'type': obj.type
    }}
    
    # 获取元数据
    if 'guide_metadata' in obj:
        try:
            obj_data['metadata'] = json.loads(obj['guide_metadata'])
        except:
            obj_data['metadata'] = obj['guide_metadata']
    else:
        obj_data['metadata'] = None
    
    print(json.dumps(obj_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if "✗" in result:
            return result
            
        try:
            import json
            lines = result.strip().split('\n')
            for line in lines:
                if line.startswith('{'):
                    return json.loads(line)
        except:
            pass
        
        return result
    
    def get_raw_guides_data(self):
        """获取所有引导线的原始数据"""
        script = """
import bpy
import json

guides = []
for obj in bpy.data.objects:
    if obj.name.startswith('LAYOUT_GUIDE_'):
        guide_data = {
            'name': obj.name,
            'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
            'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
            'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
            'type': obj.type
        }
        
        # 获取元数据
        if 'guide_metadata' in obj:
            try:
                guide_data['metadata'] = json.loads(obj['guide_metadata'])
            except:
                guide_data['metadata'] = obj['guide_metadata']
        else:
            guide_data['metadata'] = None
            
        guides.append(guide_data)

guides_data = {
    'total_count': len(guides),
    'guides': guides
}

print(json.dumps(guides_data, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if result.startswith("✗"):
            return result
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result
    
    def get_scene_boundaries(self):
        """获取场景边界的原始坐标"""
        script = """
import bpy

if not bpy.data.objects:
    print("场景为空")
else:
    # 计算边界
    locations = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            locations.append([obj.location.x, obj.location.y, obj.location.z])
    
    if locations:
        min_x = min(loc[0] for loc in locations)
        max_x = max(loc[0] for loc in locations)
        min_y = min(loc[1] for loc in locations)
        max_y = max(loc[1] for loc in locations)
        min_z = min(loc[2] for loc in locations)
        max_z = max(loc[2] for loc in locations)
        
        boundaries = {
            'min': [round(min_x, 3), round(min_y, 3), round(min_z, 3)],
            'max': [round(max_x, 3), round(max_y, 3), round(max_z, 3)],
            'size': [round(max_x - min_x, 3), round(max_y - min_y, 3), round(max_z - min_z, 3)],
            'center': [round((max_x + min_x)/2, 3), round((max_y + min_y)/2, 3), round((max_z + min_z)/2, 3)]
        }
        
        import json
        print(json.dumps(boundaries))
    else:
        print("无网格对象")
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        if "场景为空" in result or "无网格对象" in result:
            return result
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result
    
    # ========== 基本操作接口（保持简洁） ==========
    
    def create_guide_cube(self, name, location, dimensions, metadata=None, rotation=[0, 0, 0]):
        """创建线框式引导线"""
        import json
        
        metadata_json = ""
        if metadata:
            metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        # 构建代码片段 - 创建线框引导线
        code_parts = [
            "import bpy",
            "import bmesh",
            "import json",
            "",
            "# 创建新的网格",
            f'mesh = bpy.data.meshes.new("{name}_mesh")',
            f'obj = bpy.data.objects.new("{name}", mesh)',
            "bpy.context.collection.objects.link(obj)",
            "",
            "# 手动创建线框立方体的顶点和边",
            "bm = bmesh.new()",
            "",
            "# 创建立方体的8个顶点（底部对齐）",
            "v0 = bm.verts.new((-0.5, -0.5, 0.0))",
            "v1 = bm.verts.new((0.5, -0.5, 0.0))",
            "v2 = bm.verts.new((0.5, 0.5, 0.0))",
            "v3 = bm.verts.new((-0.5, 0.5, 0.0))",
            "v4 = bm.verts.new((-0.5, -0.5, 1.0))",
            "v5 = bm.verts.new((0.5, -0.5, 1.0))",
            "v6 = bm.verts.new((0.5, 0.5, 1.0))",
            "v7 = bm.verts.new((-0.5, 0.5, 1.0))",
            "",
            "# 创建立方体的12条边",
            "# 底面边",
            "bm.edges.new([v0, v1])",
            "bm.edges.new([v1, v2])",
            "bm.edges.new([v2, v3])",
            "bm.edges.new([v3, v0])",
            "# 顶面边",
            "bm.edges.new([v4, v5])",
            "bm.edges.new([v5, v6])",
            "bm.edges.new([v6, v7])",
            "bm.edges.new([v7, v4])",
            "# 垂直边",
            "bm.edges.new([v0, v4])",
            "bm.edges.new([v1, v5])",
            "bm.edges.new([v2, v6])",
            "bm.edges.new([v3, v7])",
            "",
            "# 确保bmesh有效",
            "bm.verts.ensure_lookup_table()",
            "bm.edges.ensure_lookup_table()",
            "",
            "# 将bmesh数据写入网格",
            "bm.to_mesh(mesh)",
            "bm.free()",
            "",
            "# 更新网格",
            "mesh.update()",
            "",
            "# 设置位置",
            f"obj.location = ({location[0]}, {location[1]}, {location[2]})",
            "",
            "# 设置旋转（在缩放之前）",
            f"obj.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})",
            "",
            "# 设置缩放到目标尺寸", 
            f"obj.scale = ({dimensions[0]}, {dimensions[1]}, {dimensions[2]})",
            "",
            "# 不应用变换，保持与实际物体的变换处理方式一致",
            "# bpy.context.view_layer.objects.active = obj",
            "# bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)",
            "",
            "# 创建线框材质",
            f'mat = bpy.data.materials.new(name="{name}_wireframe_material")',
            "mat.use_nodes = True",
            "nodes = mat.node_tree.nodes",
            "links = mat.node_tree.links",
            "",
            "# 清除默认节点",
            "nodes.clear()",
            "",
            "# 添加Wireframe节点",
            'wireframe_node = nodes.new(type="ShaderNodeWireframe")',
            "wireframe_node.location = (0, 0)",
            "wireframe_node.inputs[0].default_value = 0.02  # 线条粗细",
            "",
            "# 添加Emission节点",
            'emission_node = nodes.new(type="ShaderNodeEmission")',
            "emission_node.location = (200, 0)",
            "emission_node.inputs[0].default_value = (0.2, 0.8, 0.2, 1.0)  # 绿色",
            "emission_node.inputs[1].default_value = 1.0  # 强度",
            "",
            "# 添加Transparent节点",
            'transparent_node = nodes.new(type="ShaderNodeBsdfTransparent")',
            "transparent_node.location = (200, -150)",
            "",
            "# 添加Mix节点",
            'mix_node = nodes.new(type="ShaderNodeMixShader")',
            "mix_node.location = (400, 0)",
            "",
            "# 添加Material Output节点",
            'output_node = nodes.new(type="ShaderNodeOutputMaterial")',
            "output_node.location = (600, 0)",
            "",
            "# 连接节点",
            "links.new(wireframe_node.outputs[0], mix_node.inputs[0])  # Wireframe -> Mix Factor",
            "links.new(emission_node.outputs[0], mix_node.inputs[1])   # Emission -> Mix Shader 1",
            "links.new(transparent_node.outputs[0], mix_node.inputs[2]) # Transparent -> Mix Shader 2",
            "links.new(mix_node.outputs[0], output_node.inputs[0])     # Mix -> Material Output",
            "",
            "# 应用材质",
            "obj.data.materials.append(mat)",
            "",
            "# 设置显示模式为线框",
            "obj.display_type = 'WIRE'",
            "obj.show_wire = True"
        ]
        
        # 只在有元数据时添加元数据设置
        if metadata_json:
            code_parts.extend([
                "",
                "# 设置元数据",
                f'obj["guide_metadata"] = """{metadata_json}"""'
            ])
        
        code = "\n".join(code_parts)
        
        return self.send_command("execute_code", {"code": code})
    
    def move_object(self, name, new_location):
        """移动对象到新位置"""
        script = f"""
import bpy

obj = bpy.data.objects.get("{name}")
if not obj:
    print("✗ 未找到对象")
else:
    old_location = [obj.location.x, obj.location.y, obj.location.z]
    obj.location = ({new_location[0]}, {new_location[1]}, {new_location[2]})
    
    import json
    result = {{
        'object': obj.name,
        'old_location': old_location,
        'new_location': [{new_location[0]}, {new_location[1]}, {new_location[2]}]
    }}
    print(json.dumps(result))
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def scale_object(self, name, scale_factors):
        """缩放对象到指定绝对尺寸
        
        Parameters:
            name: 对象名称
            scale_factors: 目标绝对尺寸 [x, y, z] (米) 或 单一数值（等比缩放到该尺寸）
        """
        # 处理单一数值的等比缩放
        if isinstance(scale_factors, (int, float)):
            scale_factors = [scale_factors, scale_factors, scale_factors]
        
        script = f"""
import bpy

obj = bpy.data.objects.get("{name}")
if not obj:
    print("✗ 未找到对象")
else:
    # 获取当前尺寸
    current_dimensions = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
    target_dimensions = [{scale_factors[0]}, {scale_factors[1]}, {scale_factors[2]}]
    
    # 检查是否有极大的尺寸（可能是导入问题）
    max_current = max(current_dimensions)
    if max_current > 1000:  # 如果任何尺寸超过1000米，可能是单位问题
        print(f"⚠️ 检测到极大对象 (最大尺寸: {{max_current:.1f}}m)，可能存在单位转换问题")
    
    # 计算所需的缩放比例
    scale_ratios = []
    for i in range(3):
        if current_dimensions[i] > 0.001:  # 避免除零
            ratio = target_dimensions[i] / current_dimensions[i]
            scale_ratios.append(ratio)
        else:
            scale_ratios.append(1.0)
    
    # 应用缩放
    old_scale = [obj.scale.x, obj.scale.y, obj.scale.z]
    obj.scale = (scale_ratios[0], scale_ratios[1], scale_ratios[2])
    
    # 更新场景
    bpy.context.view_layer.update()
    
    # 获取缩放后的实际尺寸
    new_dimensions = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
    
    import json
    result = {{
        'object': obj.name,
        'old_dimensions': [round(d, 3) for d in current_dimensions],
        'target_dimensions': [round(d, 3) for d in target_dimensions],
        'new_dimensions': [round(d, 3) for d in new_dimensions],
        'scale_ratios': [round(r, 6) for r in scale_ratios],
        'old_scale': [round(s, 6) for s in old_scale],
        'new_scale': [round(obj.scale.x, 6), round(obj.scale.y, 6), round(obj.scale.z, 6)],
        'status': 'success'
    }}
    
    # 验证结果
    tolerance = 0.1  # 10cm 容差
    success = all(abs(new_dimensions[i] - target_dimensions[i]) < tolerance for i in range(3))
    
    if success:
        print("✓ 缩放成功")
    else:
        print("⚠️ 缩放可能不准确")
        result['status'] = 'warning'
    
    print(json.dumps(result))
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def rotate_object(self, name, rotation_euler):
        """旋转对象（向后兼容的欧拉角接口）
        
        Parameters:
            name: 对象名称
            rotation_euler: 欧拉角旋转 [x, y, z] (弧度)
        """
        return self.rotate_object_unified(name, rotation_euler, 'XYZ')
    
    def rotate_object_unified(self, name, rotation_value, rotation_mode='XYZ', force_mode=None):
        """统一旋转对象接口
        
        Parameters:
            name: 对象名称
            rotation_value: 旋转值列表
            rotation_mode: 旋转值的模式
            force_mode: 强制对象使用的旋转模式
        """
        script = f"""
import bpy
import sys
import json

# 导入RotationManager
sys.path.append('/Users/yingcongchen/Documents/code/AI原生开发/EnvisionCore-evolve/FractFlow/tools/core/blender_3')
from rotation_manager import rotation_manager

obj = bpy.data.objects.get("{name}")
if not obj:
    print(json.dumps({{"success": False, "error": "未找到对象"}}))
else:
    # 获取旋转前的状态
    old_mode = rotation_manager.detect_rotation_mode(obj)
    old_rotation, _ = rotation_manager.get_rotation_value(obj)
    
    # 使用RotationManager设置旋转
    result = rotation_manager.set_rotation_unified(
        obj, 
        {rotation_value}, 
        "{rotation_mode}",
        "{force_mode}" if "{force_mode}" != "None" else None
    )
    
    # 添加额外信息
    if result['success']:
        result['old_mode'] = old_mode
        result['old_rotation'] = old_rotation
    
    print(json.dumps(result))
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def set_guide_metadata(self, object_name, metadata):
        """设置引导线对象的元数据"""
        import json
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        script = f"""
import bpy

obj = bpy.data.objects.get("{object_name}")
if not obj:
    print("✗ 未找到对象")
else:
    obj['guide_metadata'] = '''{metadata_json}'''
    print("✓ 元数据已更新")
"""
        
        return self.send_command("execute_code", {"code": script})
    
    def find_objects_near_location(self, center, radius=2.0):
        """查找指定位置附近的对象"""
        script = f"""
import bpy
import json
import math

center = [{center[0]}, {center[1]}, {center[2]}]
radius = {radius}

nearby_objects = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        distance = math.sqrt(
            (obj.location.x - center[0])**2 + 
            (obj.location.y - center[1])**2 + 
            (obj.location.z - center[2])**2
        )
        
        if distance <= radius:
            obj_data = {{
                'name': obj.name,
                'location': [round(obj.location.x, 3), round(obj.location.y, 3), round(obj.location.z, 3)],
                'dimensions': [round(obj.dimensions.x, 3), round(obj.dimensions.y, 3), round(obj.dimensions.z, 3)],
                'rotation': [round(obj.rotation_euler.x, 3), round(obj.rotation_euler.y, 3), round(obj.rotation_euler.z, 3)],
                'distance': round(distance, 3)
            }}
            
            # 获取元数据
            if 'guide_metadata' in obj:
                try:
                    obj_data['metadata'] = json.loads(obj['guide_metadata'])
                except:
                    obj_data['metadata'] = obj['guide_metadata']
            else:
                obj_data['metadata'] = None
                
            nearby_objects.append(obj_data)

result = {{
    'center': center,
    'radius': radius,
    'count': len(nearby_objects),
    'objects': nearby_objects
}}

print(json.dumps(result, ensure_ascii=False))
"""
        
        result = self.send_command("execute_code", {"code": script})
        
        try:
            import json
            return json.loads(result.strip().split('\n')[-1])
        except:
            return result

    # ========== 添加缺失的方法（极简实现，返回原始数据） ==========
    
    def get_object_description(self, name):
        """获取对象的原始数据作为描述"""
        raw_data = self.get_raw_object_data(name)
        if isinstance(raw_data, dict):
            return f"✓ 对象 {name} 的原始数据：{raw_data}"
        else:
            return raw_data  # 如果是错误信息，直接返回
    
    def get_guide_info_by_semantic_id(self, semantic_id):
        """获取引导线信息，提供原始数据让LLM自主分析匹配"""
        guides_data = self.get_raw_guides_data()
        
        if isinstance(guides_data, dict):
            return f"引导线数据查询 (查找: '{semantic_id}'):\n{json.dumps(guides_data, ensure_ascii=False, indent=2)}"
        else:
            return f"无法获取引导线数据: {guides_data}"
    
    def find_empty_guides(self, item_type=""):
        """查找空置引导线，返回原始数据让LLM分析"""
        guides_data = self.get_raw_guides_data()
        
        if isinstance(guides_data, dict) and 'guides' in guides_data:
            filter_info = f" (筛选类型: {item_type})" if item_type else ""
            return f"✓ 查找空置引导线{filter_info}：\n原始引导线数据：{guides_data}"
        else:
            return f"✗ 无法获取引导线数据：{guides_data}"
    
    def merge_objects(self, object_list, target_name):
        """合并对象，使用Blender的join操作"""
        if not object_list or len(object_list) < 2:
            return "✗ 需要至少2个对象进行合并"
        
        # 构建对象列表字符串
        objects_str = "', '".join(object_list)
        
        script = f"""
import bpy

# 获取要合并的对象
objects_to_merge = []
for obj_name in ['{objects_str}']:
    obj = bpy.data.objects.get(obj_name)
    if obj and obj.type == 'MESH':
        objects_to_merge.append(obj)

if len(objects_to_merge) < 2:
    print("✗ 找不到足够的网格对象进行合并")
else:
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects_to_merge:
        obj.select_set(True)
    
    # 设置第一个对象为活动对象
    bpy.context.view_layer.objects.active = objects_to_merge[0]
    
    # 执行合并
    bpy.ops.object.join()
    
    # 重命名合并后的对象
    merged_obj = bpy.context.active_object
    if merged_obj:
        merged_obj.name = "{target_name}"
        print(f"✓ 成功合并对象，新名称：{{merged_obj.name}}")
    else:
        print("✗ 合并操作失败")
"""
        
        return self.send_command("execute_code", {"code": script})


blender_primitive = BlenderPrimitive() 