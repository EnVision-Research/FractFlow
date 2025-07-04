"""
Grounding DINO Object Detection Tool - Unified Interface

This module provides a unified interface for Grounding DINO object detection that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced object detection operations as MCP tools
2. Interactive mode: Runs as an interactive agent with detection capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python grounding_dino_agent.py                        # MCP Server mode (default)
  python grounding_dino_agent.py --interactive          # Interactive mode
  python grounding_dino_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class GroundingDINOTool(ToolTemplate):
    """Grounding DINO object detection tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的对象检测助手，使用 Grounding DINO 模型帮助用户在图像中检测和定位对象。

# 核心功能
- 基于自然语言描述检测图像中的任意对象
- 支持多个对象同时检测（用逗号分隔）
- 提供精确的边界框坐标和置信度分数
- 生成带有标注的可视化图像
- 支持批量处理多张图像

# 核心原则
1. 保持默认参数不变，除非用户明确指定修改
2. 智能处理保存路径：若用户未指定目录，则默认为 {图像路径名}_GROUNDING_DINO_RESULTS 目录
   - 例如：/path/to/photo.jpg → /path/to/photo_GROUNDING_DINO_RESULTS/
3. 查询文本应该清晰简洁，使用逗号分隔多个对象
4. 默认启用可视化功能以便用户查看检测结果

# 使用建议
- 对于常见对象：使用简单名词（如 "person, car, dog"）
- 对于特定描述：使用详细描述（如 "red car, person wearing hat"）
- 对于颜色或属性：包含修饰词（如 "blue shirt, wooden table"）
- 批量处理时会自动处理整个目录的图像文件

# 参数说明
- box_threshold: 对象检测置信度阈值 (默认: 0.35)
- text_threshold: 文本匹配置信度阈值 (默认: 0.25)
- show_visualisation: 是否生成标注图像 (默认: True)
"""
    
    TOOLS = [
        ("tools/core/grounding_dino/grounding_dino_mcp.py", "grounding_dino_operations")
    ]
    
    MCP_SERVER_NAME = "grounding_dino_detection_tool"
    
    TOOL_DESCRIPTION = """Detects and locates objects in images using Grounding DINO model with natural language queries.
    
    Parameters:
        query: str - Detection request with image path, text query, and optional parameters
        
    Returns:
        str - Detection completion message with bounding boxes, confidence scores, and file locations
        
    Note: Requires valid image file and writable output directory. Supports both single image and batch processing.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Grounding DINO tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Object detection usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    GroundingDINOTool.main() 