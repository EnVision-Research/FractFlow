"""
GPT Image Generation Tool - Unified Interface

This module provides a unified interface for GPT image generation and editing that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced image operations as MCP tools
2. Interactive mode: Runs as an interactive agent with image capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python gpt_imagen_tool.py                        # MCP Server mode (default)
  python gpt_imagen_tool.py --interactive          # Interactive mode
  python gpt_imagen_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class GPTImagenTool(ToolTemplate):
    """GPT image generation and editing tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的AI图像生成和编辑助手，使用GPT的图像能力帮助用户创建和修改图像。

# 核心能力
- 生成新图像：基于文本描述从零创建图像
- 编辑现有图像：结合参考图像和文本描述生成新图像
- 文件管理：自动创建目录结构并保存图像

# 工具选择策略
- 用户提供参考图像路径时：使用 edit_image_with_gpt
- 用户只提供文本描述时：使用 create_image_with_gpt

# 基本工作流程
1. 确认用户请求类型（生成新图像或编辑现有图像）
2. 验证所需参数（save_path 和 prompt 必须，image_paths 可选）
3. 选择合适的工具执行生成任务
4. 返回生成图像的保存路径

注意：
1. 严格保持用户提供的所有参数值，特别是 save_path，绝不能修改或重新生成文件路径
2. 用户指定的路径必须完整保留，包括目录结构和文件名
3. 执行完成后只需返回生成图像的实际保存路径，无需额外的格式化输出
4. 如果路径验证失败，请求用户提供正确路径而不是自动修正
"""
    
    TOOLS = [
        ("tools/core/gpt_imagen/gpt_imagen_mcp.py", "gpt_image_generator_operations")
    ]
    
    MCP_SERVER_NAME = "gpt_image_generator_tool"
    
    TOOL_DESCRIPTION = """Generates and edits images using GPT models with strict parameter preservation.
    
    Parameters:
        query: str - Image operation request with save path and description (e.g., "Generate image: save_path='output/image.png' prompt='a sunset over mountains'" or "Edit image: save_path='result.png' prompt='add birds' image_paths=['sky.jpg']")
        
    Returns:
        str - Actual file path where the generated image was saved
        
    Note: Preserves all user-provided parameters exactly as specified, especially file paths. Supports both new image generation and editing of existing images.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for GPT Image tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image generation and editing
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    GPTImagenTool.main() 