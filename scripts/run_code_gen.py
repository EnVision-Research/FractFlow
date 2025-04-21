#!/usr/bin/env python3
"""
run_simple_example.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Example script demonstrating how to use the FractalFlow Agent interface with basic setup and usage.
License: MIT License
"""

"""
Example script demonstrating how to use the FractalFlow Agent interface.

This example shows the basic setup and usage of the FractalFlow Agent
as described in the interface requirements.
"""

import asyncio
import os
import os.path as osp
from dotenv import load_dotenv
import sys
import logging

# Add the project root directory to the Python path
project_root = osp.abspath(osp.join(osp.dirname(__file__), '..'))
sys.path.append(project_root)

from FractFlow.infra.logging_utils import setup_logging, get_logger

# 设置日志
setup_logging(
    level=logging.WARNING,  # 根logger设置为INFO
    namespace_levels={
        "FractFlow": logging.DEBUG,  
        "tools": logging.DEBUG,
        "httpx": logging.WARNING,    
    }
)


# Import the FractalFlow Agent
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def main():
    # 1. Load environment variables 
    load_dotenv()
    
    # 3. Create a new agent
    agent = Agent()  # No need to specify provider here if it's in config
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['agent']['custom_system_prompt'] = 'Given a request about coding, you should use the coordinator_agent to generate the code.'

    config['deepseek']['model'] = 'deepseek-chat'
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 100  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    # Add tools to the agent
    agent.add_tool("./tools/codegen/coordinator_agent.py")
    # Initialize the agent (starts up the tool servers)
    print("Initializing agent...")
    await agent.initialize()
    
    try:
        # Interactive chat loop
        print("Agent chat started. Type 'exit', 'quit', or 'bye' to end the conversation.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ('exit', 'quit', 'bye'):
                break
                
            print("\n thinking... \n", end="")
            result = await agent.process_query(user_input)
            print("Agent: {}".format(result))
    finally:
        # Shut down the agent gracefully
        await agent.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    asyncio.run(main()) 