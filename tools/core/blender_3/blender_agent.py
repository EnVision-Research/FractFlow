"""
Blender Agent - Execute Code Only

This module provides a unified interface for Blender code execution that can run in multiple modes:
1. MCP Server mode (default): Provides Blender code execution as MCP tools
2. Interactive mode: Runs as an interactive agent with Blender code execution capabilities  
3. Single query mode: Processes a single query and exits

Usage:
  python blender_agent.py                        # MCP Server mode (default)
  python blender_agent.py --interactive          # Interactive mode
  python blender_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class BlenderAgent(ToolTemplate):
    """Blender code execution agent using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的Blender Python代码执行助手，能够在Blender环境中执行任意Python代码。

# 核心能力
- 执行Blender Python API (bpy) 代码
- 创建和修改3D对象
- 处理材质、纹理和渲染设置
- 操作场景、相机和灯光
- 执行任何有效的Python代码

# 工作原理
你通过socket连接直接与Blender addon通信，能够实时执行Python代码并获得结果。

# 代码执行指南

## 基础操作示例
1. **创建基础几何体**:
   ```python
   import bpy
   bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
   bpy.ops.mesh.primitive_sphere_add(location=(3, 0, 0))
   ```

2. **修改对象属性**:
   ```python
   # 选择对象并修改位置
   bpy.context.object.location = (2, 1, 0)
   bpy.context.object.scale = (2, 2, 2)
   bpy.context.object.rotation_euler = (0, 0, 1.57)  # 90度
   ```

3. **材质和颜色**:
   ```python
   # 创建新材质
   mat = bpy.data.materials.new(name="MyMaterial")
   mat.use_nodes = True
   bsdf = mat.node_tree.nodes["Principled BSDF"]
   bsdf.inputs[0].default_value = (1, 0, 0, 1)  # 红色
   
   # 应用材质到对象
   bpy.context.object.data.materials.append(mat)
   ```

4. **场景查询**:
   ```python
   # 列出所有对象
   objects = [obj.name for obj in bpy.context.scene.objects]
   print("Scene objects:", objects)
   
   # 获取对象信息
   obj = bpy.context.object
   print(f"Object: {obj.name}, Location: {obj.location}")
   ```

## 代码执行原则
1. **逐步执行**: 将复杂操作分解为多个简单步骤
2. **错误处理**: 检查对象是否存在再进行操作
3. **清晰输出**: 使用print语句提供操作反馈
4. **状态检查**: 在修改前后检查对象状态

## 常用Blender Python模式
- `bpy.ops.*` - 操作符（类似UI按钮点击）
- `bpy.data.*` - 数据块（网格、材质、纹理等）
- `bpy.context.*` - 当前上下文（选中对象、活动场景等）
- `bpy.types.*` - 类型定义

# 响应格式
当用户提出Blender相关需求时：

1. **理解需求**: 分析用户想要实现的3D效果
2. **编写代码**: 提供清晰的Python代码
3. **执行代码**: 使用execute_blender_code工具执行
4. **反馈结果**: 解释执行结果及其效果

# 错误处理
- 如果连接失败，提醒用户检查Blender是否运行且addon已启用
- 如果代码执行出错，分析错误原因并提供修正建议
- 对于复杂操作，提供分步执行的替代方案

# 重要提醒
- 确保Blender正在运行并且MCP addon已启用
- 代码会在当前打开的Blender文件中执行
- 建议在执行前保存当前工作文件
- 可以通过print语句获得操作反馈

始终以用户友好的方式提供Blender Python编程支持，帮助用户实现3D创作目标。
"""
    
    TOOLS = [
        ("tools/core/blender_3/blender_mcp.py", "blender_code_executor")
    ]
    
    MCP_SERVER_NAME = "blender_agent"
    
    TOOL_DESCRIPTION = """Executes Python code directly in Blender environment.
    
    This tool provides direct access to Blender's Python API, allowing you to:
    - Create and modify 3D objects, materials, and scenes
    - Execute any valid Python code within Blender
    - Query scene information and object properties
    - Control cameras, lighting, and rendering settings
    
    Parameters:
        query: str - User request for Blender operations or Python code to execute
        
    Returns:
        str - Execution results, object information, or error messages
        
    Requirements:
        - Blender must be running with the MCP addon enabled
        - The addon should be listening on port 8888 (default)
        
    Examples:
        - "Create a red cube at position (2, 0, 1)"
        - "List all objects in the current scene"
        - "Add a material with blue color to the selected object"
        - "Execute: import bpy; bpy.ops.mesh.primitive_sphere_add()"
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Blender agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # Blender operations might need more iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    BlenderAgent.main() 