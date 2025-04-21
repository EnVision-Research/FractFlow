#!/usr/bin/env python3
"""
run_fractal_example.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Example script demonstrating how to use the FractalFlow Agent interface with fractal weather tool.
License: MIT License
"""

"""
Example script demonstrating how to use the FractalFlow Agent interface.

This example shows the basic setup and usage of the FractalFlow Agent
as described in the interface requirements.
"""

import asyncio
import os
from dotenv import load_dotenv

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
    config['deepseek']['model'] = 'deepseek-chat'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    # You can modify configuration values directly
    config['agent']['max_iterations'] = 100  # Properly set as nested value
    # 4. Set configuration loaded from environment
    agent.set_config(config)
    
    
    agent.add_tool("./tools/fractal_weather_tool.py")
    print("Added fractal_weather tool")
    
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