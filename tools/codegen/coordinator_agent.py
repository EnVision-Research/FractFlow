"""
Coordinator Agent implementation for ChatToolGen.

Provides a flexible framework for tool generation by dynamically incorporating
specialized agents defined as tools, with workflow defined by system prompts.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import mcp
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 导入FractFlow Agent类，用于调用其他Agent
from FractFlow.agent import Agent

from FractFlow.infra.logging_utils import get_logger

logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Code Generator")

@mcp.resource("code_gen_coordinator://{name}/path")
def get_code_path(name: str) -> str:
    """
    Get the path where generated code should be saved.
    
    Args:
        name: Name of the code being generated
        
    Returns:
        Path where the generated code should be saved
    """
    # Create path in tools directory relative to project root
    code_path = os.path.join(project_root, "tools", f"{name}")
    return code_path


@mcp.tool()
async def code_gen_coordinator(user_input: str) -> str:
    """
    Given a request about coding, coordinate multipole LLM to generate the code.

    Args:
        user_input: Natural language description of the desired code
        
    Returns:
        A message describing the generated code, with file path
    """
    # Load environment variables
    load_dotenv()
    
    # Create an agent instance
    agent = Agent('coordinator_agent')
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 10 
    config['agent']['custom_system_prompt'] = """
General workflow:
1. Think step by step to understand the user's request.
2. Make a plan to generate the code.
3. Analyze the folder structure, and use tools to create the folders. 
4. Take an action based on the plan, then use the implementation_agent to generate the code. Note that the information given to the implementation_agent should be concise and clear. 

NOTE： before taking any action, you should think step by step.
"""
    agent.set_config(config)
    agent.add_tool(os.path.join(current_dir, "implementation_agent.py"))
    agent.add_tool(os.path.join(current_dir, "tools.py"))
    
    # Initialize the agent
    await agent.initialize()
    
    try:
        # Process the user request, letting the agent decide which tools to use
        # based on the workflow defined in the system prompt
        prompt = f"""
User wants to generate a tool with this description: 

"{user_input}"

General workflow:
1. Think step by step to understand the user's request.
2. Make a plan to generate the code.
3. Analyze the folder structure, and use tools to create the folders. 
4. Take an action based on the plan, then use the implementation_agent to generate the code. Note that the information given to the implementation_agent should be concise and clear. 

NOTE： before taking any action, you should think step by step.
"""
        result = await agent.process_query(prompt)
        return result
    finally:
        # Shut down the agent
        await agent.shutdown()

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 