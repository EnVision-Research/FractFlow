# FractFlow

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive combinations.

## Design Philosophy

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive combinations.

Each agent not only has cognitive capabilities but also the ability to call other agents, forming a self-referential, self-organizing, and self-adaptive intelligence flow.

Similar to an octopus where each tentacle has its own brain in a collaborative structure, FractFlow achieves a structurally malleable and behaviorally evolving form of distributed intelligence through the combination and coordination of modular intelligence.

## Installation

### Method 1: Local Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Method 2: Build and Install Package

```bash
python -m build 
```

Then you will get a dist folder, which can be installed with the following command:

```bash
uv pip install dist/FractFlow-0.1.0-py3-none-any.whl
```

### Method 3: Development Mode Installation

For development purposes, you can install the package in development mode. This allows you to modify the code without reinstalling the package:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
pip install -e .
```

After installation, you can run the example scripts from the `scripts` directory:

```bash
python scripts/run_simple_example.py
python scripts/run_code_gen.py
python scripts/run_fractal_example.py
python scripts/run_simple_example_ui.py
```

Note: Make sure you are in the project root directory when running these commands.

## Quick Start

First, you need to obtain API keys for language models. Currently, DeepSeek and Qwen models are supported. DeepSeek models are preferred, as Qwen has not been fully tested yet.

### Configuring API Keys

Create a .env file in the root directory and add the following content:

```bash
DEEPSEEK_API_KEY=your_api_key
QWEN_API_KEY=your_api_key
```

### Creating and Running a Simple Agent

Here is a basic example showing how to create and use a FractFlow Agent:

```python
import asyncio
import os
from dotenv import load_dotenv
from FractFlow.agent import Agent

async def main():
    # Load environment variables
    load_dotenv()
    
    # Create Agent
    agent = Agent()
    config = agent.get_config()
    # Default configurations can be overwritten as needed
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # Add tools
    agent.add_tool("./tools/weather/forecast.py")
    
    # Initialize Agent
    await agent.initialize()
    
    try:
        # Process user query
        result = await agent.process_query("I want to know the weather forecast for Beijing")
        print(f"Agent: {result}")
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## How to Write Tools

FractFlow uses the MCP protocol to define tools. Tools can be separate Python files written according to the MCP server protocol.

### Tool Example

Here is an example of a weather forecast tool (refer to `tools/forecast.py`):

```python
from typing import Any, Dict
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# API constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with error handling"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a specific location
    
    Args:
        latitude: The latitude of the location
        longitude: The longitude of the location
    """
    # Get forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    
    if not points_data:
        return "Unable to retrieve forecast data for this location."
    
    # Get forecast URL from points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data:
        return "Unable to retrieve detailed forecast."
    
    # Format periods into readable forecasts
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show the next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

### Tool Development Standards

1. Use the `FastMCP` class to create a tool server
2. Use the `@mcp.tool()` decorator to define tool functions
3. Provide clear function documentation and parameter descriptions
4. Tool functions should be asynchronous (`async def`)
5. Run the server in the `if __name__ == "__main__":` block

## Using the FractFlow Library

Here is a more complete example of how to use the FractFlow library (refer to `run_simple_example.py`):

```python
import asyncio
import os
from dotenv import load_dotenv
from FractFlow.agent import Agent

async def main():
    # Load environment variables
    load_dotenv()
    
    # Create Agent
    agent = Agent()
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['qwen']['api_key'] = os.getenv('QWEN_API_KEY')
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # Add tools
    if os.path.exists("./tools/weather/forecast.py"):
        agent.add_tool("./tools/weather/forecast.py")
        print("Added weather tool")
    
    # Initialize Agent
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
        # Gracefully shut down the Agent
        await agent.shutdown()
        print("\nAgent chat ended.")

if __name__ == "__main__":
    asyncio.run(main())
```

### Main API Methods

- `agent = Agent()` - Create a new Agent instance
- `config = agent.get_config()` - Get current configuration
- `agent.set_config(config)` - Set configuration
- `agent.add_tool(tool_path)` - Add a tool to the Agent
- `await agent.initialize()` - Initialize the Agent
- `result = await agent.process_query(user_input)` - Process user query
- `await agent.shutdown()` - Shut down the Agent

## Advanced Usage: Agent as a Tool

A powerful feature of FractFlow is that Agents themselves can be used as more intelligent tools by other Agents, forming a fractal architecture. Here's an example (refer to `fractal_weather_tool.py`):

```python
import asyncio
import os
import sys
from dotenv import load_dotenv
from FractFlow.agent import Agent
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fractal weather")

@mcp.tool()
async def weather_agent(user_input: str) -> str:
    """
    This function takes user input and returns weather forecasts.
    Args:
        user_input: User's input
    Returns:
        Weather forecast results
    """
    # Load environment variables
    load_dotenv()
    
    # Create Agent
    agent = Agent()
    config = agent.get_config()
    config['agent']['provider'] = 'deepseek'
    config['deepseek']['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    config['deepseek']['model'] = 'deepseek-chat'
    config['agent']['max_iterations'] = 100
    agent.set_config(config)
    
    # Add tools
    if os.path.exists("./tools/weather/forecast.py"):
        agent.add_tool("./tools/weather/forecast.py")
        print("Added weather tool")
    
    # Initialize Agent
    await agent.initialize()
    
    try:
        # Process user query
        result = await agent.process_query(user_input)
    finally:
        # Shut down Agent
        await agent.shutdown()
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
```

This approach allows you to create a specialized Agent tool that can be called by other Agents, forming a fractal intelligence structure. Advanced Agents can delegate tasks to specialized Agents, and each specialized Agent can use its own set of tools.

----

Supported models:
- DeepSeek (reasoner and chat)
- Qwen (qwen2.5-vl-72b-instruct, qwen-plus)


----
Updates

## Version 0.2.0
- Improved security of configuration system
- Unified DeepSeek and Qwen model implementations
- Enhanced tool calling capabilities
  - Added support for parallel multi-tool execution
  - Refactored toolCallingHelper as independent module
  - Improved DeepSeek model reasoner with better tool calling
- Updated the image_io tool