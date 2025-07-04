"""
Web Save Tool - Unified Interface

This module provides a unified interface for web search and file saving operations that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced web search and save as MCP tools
2. Interactive mode: Runs as an interactive agent with web search and file capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python web_save_tool.py                        # MCP Server mode (default)
  python web_save_tool.py --interactive          # Interactive mode
  python web_save_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class web_save_agent(ToolTemplate):
    """Web search and save tool using ToolTemplate with fractal intelligence"""
    
    SYSTEM_PROMPT = """
你是一个专业的信息收集和整理智能体。

【严格约束】
❌ 绝对禁止：在对话中直接输出或显示任何搜索结果
❌ 绝对禁止：在对话中直接显示文件内容
✅ 必须执行：所有操作必须通过工具调用完成

【强制工具调用流程】
1. 调用 search_agent 进行网页搜索和浏览
2. 调用 file_io 将整理好的内容保存到文件
3. 确认每次操作成功后继续下一步

【工具使用规范】
- search_agent：专门用于网页搜索和内容获取
- file_io：专门用于文件保存操作

【文件路径规范】
- 默认目录：output/web_save_tool/[项目名]/
- 文件命名：根据内容主题命名，使用.md或.txt格式

【操作验证】
每次工具调用后必须确认：
- search_agent：搜索是否成功，内容是否完整
- file_io：文件是否成功保存

【错误处理】
如果工具调用失败：
1. 报告具体的工具和错误信息
2. 尝试修正参数
3. 重新调用相应工具

"""
    
    # 分形智能体：调用其他智能体
    TOOLS = [
        ("tools/core/websearch/src/server.py", "search_agent"),
        ("tools/core/file_io/file_io_agent.py", "file_io")
    ]
    
    TOOL_DESCRIPTION = """
    Searches the web for information and saves the results to files with intelligent content organization.

This tool combines web search capabilities with file management to create a complete information gathering and storage workflow. It can search for current information, browse websites, and save organized content to files.

Input format:
- Natural language requests for information gathering and saving
- Can specify search topics, file formats, and organization requirements
- May include specific websites to search or file destinations
- Can request different levels of detail or specific information focus

Examples:
- "Search for the latest AI developments and save a summary to ai_trends.md"
- "Find information about sustainable energy and create a comprehensive report"
- "Research Python programming tutorials and save links and notes to a file"
- "Gather news about climate change and organize it into a structured document"
- "Search for travel information about Japan and save an itinerary file"

Features:
- Intelligent web search with follow-up browsing
- Automatic content organization and structuring
- File creation with appropriate formatting
- Multi-round search for comprehensive information gathering
- Content validation and quality assurance
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Web Save tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=20,  # Web search and save may require multiple rounds
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    web_save_agent.main() 