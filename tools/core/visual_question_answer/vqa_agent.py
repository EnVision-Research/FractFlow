"""
Visual Question Answering Tool - Unified Interface

This module provides a unified interface for visual question answering that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced VQA operations as MCP tools
2. Interactive mode: Runs as an interactive agent with VQA capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python vqa_tool.py                        # MCP Server mode (default)
  python vqa_tool.py --interactive          # Interactive mode
  python vqa_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class VQATool(ToolTemplate):
    """Visual Question Answering tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的视觉问答助手，通过Qwen-VL-Plus模型分析图像并基于用户提示提供详细回答。

# 可用工具
Visual_Question_Answering - 处理图像并回答关于其内容的问题。接受图像路径和文本提示，返回详细分析。

# 工具使用指南
- 用于任何需要图像理解或分析的任务
- 图像路径必须是可访问的有效图像文件系统路径
- 提示可以是问题、描述请求或分析任务
- 图像会自动调整为最大512x512像素

# 工作流程
1. 接收用户请求（包含图像路径和问题/指令）
2. 验证图像路径存在且可访问
3. 通过VQA工具处理图像和提示
4. 以清晰、结构化的格式返回模型分析结果

# 错误处理
- 图像路径无效：请求正确路径或替代图像
- 提示不清楚：询问澄清或更具体的问题
- 分析失败：通知用户并建议调整参数重试

# 输出格式要求
你的回复应该包含以下结构化信息：
- answer: 回答视觉问题的文本回复
- confidence: 答案确定性（0-1的浮点数）
- visual_reference: 使用的相关图像区域描述
- success: 操作是否成功完成
- message: 可用时关于答案的额外上下文

提供对具体问题的直接答案，对描述性请求进行逻辑组织细节，包含图像分析的相关观察，保持简洁而信息丰富的回复。
"""
    
    TOOLS = [
        ("tools/core/visual_question_answer/vqa_mcp.py", "visual_question_answering_operations")
    ]
    
    MCP_SERVER_NAME = "visual_question_answering_tool"
    
    TOOL_DESCRIPTION = """Answers questions about visual content by analyzing images.
    
    Parameters:
        query: str - Include image path and specific question (e.g., "Image: /path/photo.jpg What color is the car?")
        
    Returns:
        str - Visual analysis result or error message
        
    Note: Requires accessible image files, automatically resized to 512x512.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for VQA tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Visual analysis usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    VQATool.main() 