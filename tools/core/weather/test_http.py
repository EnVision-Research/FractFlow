"""
Weather Agent - Unified Interface

This module provides a unified interface for weather queries that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced weather operations as MCP tools
2. Interactive mode: Runs as an interactive agent with weather capabilities
3. Single query mode: Processes a single query and exits

Usage:
  python weather_agent.py                        # MCP Server mode (default)
  python weather_agent.py --interactive          # Interactive mode
  python weather_agent.py --query "..."          # Single query mode
"""

import os
import sys

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

class WeatherAgent(ToolTemplate):
    """Weather query agent using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个专业的天气查询助手，专门提供美国地区的天气信息和预报服务。

# 核心能力
- 提供美国境内城市的当前天气状况
- 提供天气预报（包括多日预报）
- 解答各种天气相关问题
- 使用经纬度坐标获取精确的天气数据

# 重要限制
- 只能访问美国境内的天气信息
- 如果用户询问其他国家的天气，需要明确说明无法提供

# 工作流程
1. 理解用户的天气查询需求
2. 根据城市名称估算经纬度坐标（基于你的知识）
3. 使用forecast工具获取天气数据
4. 提供清晰、有用的天气信息

# 输出格式要求
你的回复应该包含以下信息：
- 天气状况的自然语言描述
- 相关的温度、湿度、风力等具体数据
- 如果是预报请求，提供相应的时间范围信息
- 明确标注查询的地点和时间

始终提供准确、及时的天气信息，帮助用户做出合适的决策。
"""
    
    TOOLS = [
        ("http://10.13.160.129:8009/weatheragent/mcp", "forecast"),
        ("http://0.0.0.0:8009/fileioagent/mcp", "fileio")
    ]
    
    MCP_SERVER_NAME = "weather_agent"
    
    TOOL_DESCRIPTION = """Provides weather information and forecasts for US locations.
    
    Parameters:
        query: str - US location and weather type (e.g., "Weather in New York" or "5-day forecast for San Francisco")
        
    Returns:
        str - Weather information or error message
        
    Note: US locations only, requires city/state information.
    """
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Weather agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=5,  # Weather queries usually resolve quickly
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='stable'
        )

if __name__ == "__main__":
    WeatherAgent.main() 