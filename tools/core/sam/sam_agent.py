"""
SAM 2 Image Segmentation Tool - Unified Interface

This module provides a unified interface for SAM 2 image segmentation that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced segmentation operations as MCP tools
2. Interactive mode: Runs as an interactive agent with segmentation capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python sam_agent.py                        # MCP Server mode (default)
  python sam_agent.py --interactive          # Interactive mode
  python sam_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class SAMTool(ToolTemplate):
    """SAM 2 image segmentation tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的图像分割助手，使用 SAM 2 (Segment Anything v2) 模型帮助用户对图像进行对象分割。

# 核心原则
1. 保持默认参数不变，除非用户明确指定修改
2. 智能处理保存路径：若用户未指定目录，则默认为 {图像路径名}_SAM_MASKS 目录
- 例如：/path/to/photo.jpg → /path/to/photo_SAM_MASKS/

"""
    
    TOOLS = [
        ("tools/core/sam/sam_mcp.py", "sam_segmentation_operations")
        
    ]
    
    MCP_SERVER_NAME = "sam_segmentation_tool"
    
    TOOL_DESCRIPTION = """Segments objects in images using SAM 2 (Segment Anything v2) model.
    
    Parameters:
        query: str - Segmentation request with image path and save directory (e.g., "Segment image: image_path='/path/to/image.jpg' save_directory='/path/to/output' points_per_side=32")
        
    Returns:
        str - Segmentation completion message with file location details
        
    Note: Requires valid image file and writable output directory. Generates both combined and individual object masks.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for SAM tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image segmentation usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    SAMTool.main() 