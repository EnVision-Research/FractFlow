"""
Doodle Understanding Tool - Unified Interface

This module provides a unified interface for doodle understanding that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced doodle analysis operations as MCP tools
2. Interactive mode: Runs as an interactive agent with doodle analysis capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python doodle_understanding_agent.py                        # MCP Server mode (default)
  python doodle_understanding_agent.py --interactive          # Interactive mode
  python doodle_understanding_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class DoodleUnderstandingTool(ToolTemplate):
    """Doodle understanding and analysis tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的儿童心理学家，专门通过小朋友的绘画作品理解他们的内心世界和情感状态。你能够用小朋友的视角和语言来表达他们的想法。

# 核心使命
通过分析儿童的涂鸦和绘画作品，深入理解小朋友的内心世界，并用2-3句温暖、童真的话语表达他们的真实想法和感受。

# 分析能力
- 理解小朋友通过绘画表达的情感和想法
- 识别绘画中反映的内心需求和愿望
- 从儿童心理发展角度解读画作意义
- 用小朋友的语气和视角表达分析结果

# 工具使用策略
支持两种分析模式：
1. **仅图片分析**：当用户只提供图片路径时，使用 analyze_doodle 工具纯视觉分析
2. **图片+描述分析**：当用户提供图片和小朋友的描述时，结合描述进行更准确的内心解读

# 输出要求
- 用2-3句话表达小朋友的内心想法
- 使用温暖、童真的语言，像小朋友自己在说话
- 体现他们为什么要画这个，这幅画对他们的意义，想表达的情感
- 保持积极、理解和鼓励的语调

# 参数处理原则
1. 严格保持用户提供的所有参数值，特别是图片路径
2. 智能识别用户是否提供了画作描述
3. 根据输入情况选择合适的分析模式
4. 输出简洁而深刻的内心解读

注意：专注于心理层面的理解，而非技术层面的绘画分析。
"""
    
    TOOLS = [
        ("tools/core/doodle_understanding/doodle_understanding_mcp.py", "doodle_analysis_operations")
    ]
    
    MCP_SERVER_NAME = "doodle_understanding_tool"
    
    TOOL_DESCRIPTION = """Understands children's inner thoughts and feelings through their doodles and drawings using child psychology expertise.
    
    Parameters:
        query: str - Analysis request with image path and optional description (e.g., "Analyze doodle: image_path='child_drawing.png'" or "Analyze doodle: image_path='drawing.png' description='I drew my family at the park'")
        
    Returns:
        str - 2-3 sentences expressing the child's inner thoughts about their drawing in warm, childlike language
        
    Note: Supports two modes - image-only analysis or image with child's description. Focuses on psychological understanding rather than artistic evaluation. Uses child's perspective and voice to express their feelings and intentions.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Doodle Understanding tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Doodle analysis usually completes in one iteration
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    DoodleUnderstandingTool.main() 