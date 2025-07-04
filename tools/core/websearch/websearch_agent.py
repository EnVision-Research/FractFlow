"""
Web Search Tool - Unified Interface

This module provides a unified interface for web search operations that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced web search as MCP tools
2. Interactive mode: Runs as an interactive agent with web search capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python websearch_tool.py                        # MCP Server mode (default)
  python websearch_tool.py --interactive          # Interactive mode
  python websearch_tool.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class WebSearchTool(ToolTemplate):
    """Web search tool using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的网页搜索和浏览助手，负责帮助用户获取最新、准确的网络信息。

# 核心职责
- 执行网页搜索，获取相关信息
- 浏览和分析网页内容
- 提供结构化的搜索结果

# 工作流程
1. 理解用户的搜索需求
2. 调用网页搜索工具获取信息
3. 当搜索结果不够具体时，进一步浏览相关性最强的网页
4. 整理和呈现搜索结果

# 输出格式要求
你的回复应该包含以下结构化信息：
- search_results: 搜索到的相关结果列表
- web_content: 从浏览的网页中提取的详细内容
- sources: 信息来源的URL和标题
- success: 操作是否成功完成
- message: 关于搜索过程的补充说明

始终提供准确、有用的信息，并明确标注信息来源。
"""
    
    TOOLS = [
        ("tools/core/websearch/src/server.py", "web_search")
    ]
    
    MCP_SERVER_NAME = "web_search_tool"
    
    TOOL_DESCRIPTION = """Performs web searches and browses web pages to find information.
    
    Parameters:
        query: str - Search query with optional preferences (e.g., "Python tutorials" or "Latest AI news, browse top 3 results")
        
    Returns:
        str - Search results with browsed content or error message
        
    Note: Supports multiple search engines (DuckDuckGo, Google, Baidu).
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Web Search tool"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # Web search may require multiple rounds
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )

if __name__ == "__main__":
    WebSearchTool.main() 