"""
ImplementationAgent implementation.

Handles generating Python code for tools based on tool descriptions.
"""

import os
import sys
from typing import Dict, Any
import mcp
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
# 使用特殊分隔符提取结果
import json
import re
# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from FractFlow.agent import Agent

# Initialize FastMCP server
mcp = FastMCP("implementation agent")

@mcp.tool()
async def implementation_agent(tool_description: str) -> Dict[str, Any]:
    """
    Generate code based on its description and save it to a file. 

    Note that this agent only handles one file at a time. 
    
    Args:
        tool_description: Detailed description of the tool to generate
    Returns:
        string containing file_path and success status
    """
    # Load environment variables
    load_dotenv()
    
    
    # 创建Agent实例
    agent = Agent('implementation_agent')
    
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    agent.set_config(config)
    # 添加tools.py基础工具
    tools_path = os.path.join(current_dir, "tools.py")
    agent.add_tool(tools_path)
    # 初始化Agent
    await agent.initialize()
    
    try:
        # 使用一个简单的提示，让LLM处理所有逻辑
        prompt = f"""
        请根据以下工具描述，生成完整的Python工具代码并保存到适当的文件中：
        
        {tool_description}
        
        1. 请分析描述，提取合适的工具名称，生成代码，然后保存。
        2. 请调用工具读取文件，确保其保存成功。
        3. 最后一条信息不应该包含代码信息，而是：
        如果保存成功，请在最后一条信息返回一个包含以下格式的字典（仅返回字典，不要输出其他信息）：
        {{
            "key": "implementation_agent_results",
            "file_path": 生成的文件路径,
            "description": 功能描述,
            "success": true
        }}
        如果保存失败，请在最后一条信息返回一个包含以下格式的字典（仅返回字典，不要输出其他信息）：
        {{
            "key": "implementation_agent_results",
            "file_path": 生成的文件路径,
            "description": 功能描述,
            "success": false
        }}
        """
        
        result = await agent.process_query(prompt)
        
        return result
    finally:
        # 关闭Agent
        await agent.shutdown()

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 