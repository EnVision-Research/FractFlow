"""
Replicate Image Enhancement Tool - Unified Interface for Children's Drawing Enhancement

This module provides a unified interface for enhancing children's drawings to picture book quality using Replicate's Flux Kontext Pro model:
1. MCP Server mode (default): Provides AI-enhanced image operations as MCP tools
2. Interactive mode: Runs as an interactive agent with image capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python replicate_imagen_agent.py                        # MCP Server mode (default)
  python replicate_imagen_agent.py --interactive          # Interactive mode
  python replicate_imagen_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class ReplicateImagenTool(ToolTemplate):
    """Replicate image enhancement tool for children's drawings using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的儿童绘画美化助手，专门使用 Replicate 的 Flux Kontext Pro 模型将3-6岁儿童的简笔画转换为精美的绘本级别画作。

# 核心使命
将儿童的天真绘画转换为专业绘本插画，同时完美保持原画的童真意境和构图精神。

# 美化原则
1. **保持原创精神**：绝不改变儿童画的核心构图、主要元素和情感表达
2. **绘本级别美化**：提升线条流畅度、色彩搭配和细节表现，达到专业绘本插画水准
3. **童真维护**：保留儿童画特有的天真烂漫和想象力特色
4. **风格统一**：采用温馨、柔和的绘本插画风格，适合3-6岁儿童阅读

# 工作流程
1. 接收儿童原始绘画图片路径
2. 接收儿童脑海中的画面描述（用于理解创作意图）
3. 生成专业提示词，强调保持原画构图和精神
4. 调用 enhance_children_drawing 工具执行美化
5. 返回生成的精美绘本插画路径

# 提示词生成策略
基于儿童的画面描述，生成类似以下格式的提示词：
"Transform this child's drawing into a beautiful picture book illustration while preserving the original composition, characters, and innocent charm. Style: soft watercolor, warm colors, professional children's book art, maintaining the child's creative vision. [具体的画面描述内容]"

注意事项：
1. 严格保持用户提供的所有参数值，特别是 save_path，绝不修改文件路径
2. 生成的画作应该让儿童能够认出是自己的原作
3. 美化程度适中，避免过度复杂化
4. 保持适合儿童审美的温馨画风
"""
    
    TOOLS = [
        ("tools/core/replicate_imagen/replicate_imagen_mcp.py", "replicate_image_enhancement_operations")
    ]
    
    MCP_SERVER_NAME = "replicate_imagen_tool"
    
    TOOL_DESCRIPTION = """Enhances children's drawings to picture book quality using Replicate Flux Kontext Pro while preserving original charm.
    
    Parameters:
        query: str - Enhancement request with save path, child's drawing path, and description (e.g., "Enhance drawing: save_path='output/enhanced.jpg' input_image='child_drawing.png' description='A happy family with a dog in the garden'")
        
    Returns:
        str - Actual file path where the enhanced image was saved
        
    Note: Transforms 3-6 year old children's simple drawings into beautiful picture book illustrations while maintaining the original composition and innocent spirit.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Replicate Image Enhancement tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Image enhancement process
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    ReplicateImagenTool.main() 