# FractFlow

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive composition.

## Design Philosophy

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive composition.

Each agent not only possesses cognitive capabilities but also has the ability to call other agents, forming self-referential, self-organizing, and self-adaptive intelligent flows.

Similar to how each tentacle of an octopus has its own brain in a collaborative structure, FractFlow achieves structurally malleable and behaviorally evolving distributed intelligence through the combination and coordination of modular intelligence.

## Installation

Please install "uv" first: https://docs.astral.sh/uv/#installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Note: The project is still under development. If dependencies are not satisfied, please install manually: `uv pip install XXXX`.

### Advantages of uv Environment Isolation

When the tool ecosystem expands, different tools may require different dependency package versions. uv provides powerful environment isolation capabilities:

```bash
# Create independent environment for specific tools
cd tools/your_specific_tool/
uv venv
source .venv/bin/activate

# Install tool-specific dependencies
uv pip install specific_package==1.2.3

# Tool will use independent environment when running
python your_tool_agent.py
```

**Particularly useful scenarios**:
- **Third-party tool integration**: Avoid dependency conflicts when wrapping tools from other GitHub repositories
- **Version compatibility**: Different tools need different versions of the same library
- **Experimental development**: Test new dependencies without affecting the main environment

This flexible environment management allows FractFlow to support more complex and diverse tool ecosystems.

## Environment Configuration

### .env File Setup

Create a `.env` file in the project root directory to configure necessary API keys:

```bash
# Create .env file
touch .env
```

Example `.env` file content:

```env
# AI Model API Keys (configure at least one)

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API Key (for GPT models and image generation)
OPENAI_API_KEY=your_openai_api_key_here
COMPLETION_API_KEY=your_openai_api_key_here

# OpenRouter API Key (for unified access to multiple models)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Qwen API Key (Alibaba Cloud Tongyi Qianwen)
QWEN_API_KEY=your_qwen_api_key_here

# Optional: Custom API Base URLs
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### API Key Acquisition

#### DeepSeek (Recommended)
1. Visit [DeepSeek Open Platform](https://platform.deepseek.com/)
2. Register an account and obtain API key
3. Set `DEEPSEEK_API_KEY` environment variable

#### OpenAI
1. Visit [OpenAI API Platform](https://platform.openai.com/api-keys)
2. Create API key
3. Set `OPENAI_API_KEY` and `COMPLETION_API_KEY` environment variables
4. **Note**: Image generation functionality requires OpenAI API key

#### OpenRouter
1. Visit [OpenRouter Platform](https://openrouter.ai/)
2. Register an account and obtain API key
3. Set `OPENROUTER_API_KEY` environment variable
4. **Note**: OpenRouter provides unified access to multiple AI models through a single API

#### Qwen (Optional)
1. Visit [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/)
2. Enable Tongyi Qianwen service and obtain API key
3. Set `QWEN_API_KEY` environment variable

### Configuration Validation

Verify that environment configuration is correct:

```bash
# Test basic functionality
python tools/core/weather/weather_agent.py --query "How is the weather in New York?"
```

## Quick Start

### Basic Usage

Each tool in FractFlow supports three running modes:

```bash
# MCP Server mode (default, no need to start manually, usually started automatically by programs)
python tools/core/file_io/file_io_agent.py

# Interactive mode
python tools/core/file_io/file_io_agent.py --interactive

# Single query mode
python tools/core/file_io/file_io_agent.py --query "Read README.md file"
```

### First Tool Run

Let's run a simple file operation:

```bash
python tools/core/file_io/file_io_agent.py --query "Read the first 10 lines of README.md file in project root directory"
```

## Tool Development Tutorial

### 5-Minute Quick Start: Hello World Tool

Creating your first FractFlow tool only requires inheriting `ToolTemplate` and defining two required attributes:

```python
# my_hello_tool.py
import os
import sys

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class HelloTool(ToolTemplate):
    """Simple greeting tool"""
    
    SYSTEM_PROMPT = """
You are a friendly greeting assistant.
When users provide names, please give personalized greetings.
Please reply in Chinese, maintaining a friendly and enthusiastic tone.
"""
    
    TOOL_DESCRIPTION = """
Tool for generating personalized greetings.

Parameters:
    query: str - User's name or greeting request

Returns:
    str - Personalized greeting message
"""

if __name__ == "__main__":
    HelloTool.main()
```

Run your tool:

```bash
# Interactive mode
python my_hello_tool.py --interactive

# Single query
python my_hello_tool.py --query "My name is Zhang San"
```

**Core Concept Understanding:**
- `SYSTEM_PROMPT`: Defines agent behavior and response style
- `TOOL_DESCRIPTION`: **Important**: This is the tool usage manual exposed to upper-layer Agents. In fractal intelligence, upper-layer Agents read this description to understand how to call lower-layer tools
- `ToolTemplate`: Provides unified runtime framework (MCP server, interactive, single query - three modes)

### 30-Minute Practice: Three Classic Scenarios

#### Scenario 1: File Operation-Based Tool Development

**Reference Implementation**: [`tools/core/file_io/file_io_agent.py`](tools/core/file_io/file_io_agent.py)

**Extension Points**:
- Inherit `ToolTemplate` base class to get three running mode support
- Reference `file_io_mcp.py` as underlying file operation tool
- Customize `SYSTEM_PROMPT` to implement specific file analysis logic
- Configure appropriate iteration count and model parameters

**Creation Steps**:
1. Copy basic structure of file_io_agent.py
2. Modify `SYSTEM_PROMPT` to add your analysis logic (such as statistical analysis, content summarization, etc.)
3. Adjust `TOOL_DESCRIPTION` to describe new functionality features
4. Adjust parameters in `create_config()` according to task complexity

**Core Configuration Example**:
```python
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
# Add your professional analysis prompts to SYSTEM_PROMPT
```

#### Scenario 2: Image Generation Integration Tool Development

**Reference Implementation**: [`tools/core/gpt_imagen/gpt_imagen_agent.py`](tools/core/gpt_imagen/gpt_imagen_agent.py)

**Core Features**:
- Support both text-to-image and image editing modes
- Strict path parameter preservation strategy
- Automatic prompt optimization mechanism

**Customization Directions**:
- **Prompt Engineering**: Modify `SYSTEM_PROMPT` to add specific prompt optimization strategies
- **Post-processing Integration**: Combine with other image processing tools for composite functionality
- **Batch Processing**: Extend to support multi-image generation workflows
- **Style Customization**: Optimize for specific artistic styles or purposes

**Key Configuration**:
```python
TOOLS = [("tools/core/gpt_imagen/gpt_imagen_mcp.py", "gpt_image_generator_operations")]
# Define your image generation strategy in SYSTEM_PROMPT
```

#### Scenario 3: Fractal Intelligence Demonstration (Visual Article Agent)

**Complete Implementation**: [`tools/composite/visual_article_agent.py`](tools/composite/visual_article_agent.py)

**Extension Directions**:
- Add more professional tools (such as web search, data analysis)
- Implement more complex content generation strategies
- Integrate different file format outputs

**Core Understanding of Fractal Intelligence**:
- **Recursive Composition**: Tools can call other tools, forming multi-layer intelligent structures
- **Professional Division**: Each tool focuses on specific domains, achieving complex functionality through combination
- **Adaptive Coordination**: High-level tools dynamically select and combine low-level tools based on task requirements

### Deep Mastery: Architectural Principles

#### ToolTemplate Lifecycle

```python
# 1. Class Definition Phase
class MyTool(ToolTemplate):
    SYSTEM_PROMPT = "..."      # Define agent behavior
    TOOL_DESCRIPTION = "..."   # Define tool interface
    TOOLS = [...]              # Declare dependent tools

# 2. Initialization Phase
@classmethod
async def create_agent(cls):
    config = cls.create_config()           # Create configuration
    agent = Agent(config=config)           # Create agent
    await cls._add_tools_to_agent(agent)   # Add tools
    return agent

# 3. Runtime Phase
def main(cls):
    # Choose running mode based on command line arguments
    if args.interactive:
        cls._run_interactive()      # Interactive mode
    elif args.query:
        cls._run_single_query()     # Single query
    else:
        cls._run_mcp_server()       # MCP server mode
```

#### Configuration System Details

FractFlow provides three-level configuration customization:

```python
# Level 1: Use default configuration
class SimpleTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    # Automatically use DeepSeek default configuration

# Level 2: Partial customization
class CustomTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    
    @classmethod
    def create_config(cls):
        return ConfigManager(
            provider='deepseek',           # Switch model provider
            openai_model='deepseek-reasoner',       # Specify model
            max_iterations=20           # Adjust iteration count
        )

# Level 3: Full customization
class AdvancedTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    
    @classmethod
    def create_config(cls):
        from dotenv import load_dotenv
        load_dotenv()
        
        return ConfigManager(
            provider='qwen',
            anthropic_model='qwen-plus',
            max_iterations=50,
            temperature=0.7,
            custom_system_prompt=cls.SYSTEM_PROMPT + "\nAdditional instructions...",
            tool_calling_version='turbo',
            timeout=120
        )
```

## Tool Showcase

### Core Tools

#### File I/O Agent - File Operation Expert
```bash
# Basic file operations
python tools/core/file_io/file_io_agent.py --query "Read config.json file"
python tools/core/file_io/file_io_agent.py --query "Write 'Hello World' to output.txt"

# Advanced operations
python tools/core/file_io/file_io_agent.py --query "Read lines 100-200 of large file data.csv"
python tools/core/file_io/file_io_agent.py --query "Delete all lines containing 'ERROR' from temp.log"
```

**Feature Highlights**:
- Intelligent file operations: read, write, delete, insert
- Large file chunked processing
- Line-level precise operations
- Automatic directory creation

#### GPT Imagen Agent - AI Image Generation
```bash
# Image generation
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='spring_garden.png' prompt='a beautiful spring garden with flowers'"
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='robot.png' prompt='futuristic robot illustration'"
```

#### Web Search Agent - Web Search
```bash
# Web search
python tools/core/websearch/websearch_agent.py --query "Latest AI technology developments"
python tools/core/websearch/websearch_agent.py --query "Python performance optimization methods"
```

#### Weather Agent - Weather Query Assistant (US Only)
```bash
# Weather queries (US cities only)
python tools/core/weather/weather_agent.py --query "Weather in New York today"
python tools/core/weather/weather_agent.py --query "5-day forecast for San Francisco"
```

This tool can only query weather information within the United States.

#### Visual Question Answer - Visual Q&A
```bash
# Image understanding (based on Qwen-VL-Plus model)
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/image.jpg What objects are in this picture?"
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/photo.png Describe the scene in detail"
```

### Composite Tools

#### Visual Article Agent - Illustrated Article Generator

This is a typical representative of fractal intelligence, coordinating multiple tools to generate complete text-image content:

```bash
# Generate complete illustrated articles
python tools/composite/visual_article_agent.py --query "Write an article about AI development with illustrations"

# Customized articles
python tools/composite/visual_article_agent.py --query "设定：一个视觉识别AI统治社会的世界，人类只能依赖它解释图像。主人公却拥有"人类视觉直觉"，并因此被怀疑为异常个体。
要求：以第一人称，写一段剧情片段，展现他与AI模型对图像理解的冲突。
情绪基调：冷峻、怀疑、诗性。"
```


![](assets/visual_article.gif)

**Workflow**:
1. Analyze article requirements and structure
2. Use `file_manager_agent` to write chapter content
3. Use `image_creator_agent` to generate supporting illustrations
4. Integrate into complete Markdown document

**Output Example**:
```
output/visual_article_generator/ai_development/
├── article.md           # Complete article
└── images/             # Supporting images
    ├── section1-fig1.png
    ├── section2-fig1.png
    └── section3-fig1.png
```

#### Web Save Agent - Intelligent Web Saving
```bash
# Intelligent web saving (fractal intelligence example)
python tools/composite/web_save_agent.py --query "Search for latest Python tutorials and save to a comprehensive guide file"
python tools/composite/web_save_agent.py --query "Find information about machine learning and create an organized report"
```

**Feature Highlights**:
- Fractal intelligence combining web search and file saving
- Intelligent content organization and structuring
- Automatic file path management
- Multi-round search support

## API Reference

### Two Tool Development Approaches

FractFlow provides two flexible tool development approaches to meet different development needs:

#### Approach 1: Inherit ToolTemplate (Recommended)

Standardized tool development approach with automatic support for three running modes:

```python
from FractFlow.tool_template import ToolTemplate

class MyTool(ToolTemplate):
    """Standard tool class"""
    
    SYSTEM_PROMPT = """Your tool behavior instructions"""
    TOOL_DESCRIPTION = """Tool functionality description"""
    
    # Optional: depend on other tools
    TOOLS = [("path/to/tool.py", "tool_name")]
    
    @classmethod
    def create_config(cls):
        return ConfigManager(...)

# Automatically supports three running modes
# python my_tool.py                    # MCP server mode
# python my_tool.py --interactive      # Interactive mode  
# python my_tool.py --query "..."      # Single query mode
```

#### Approach 2: Custom Agent Class

Completely autonomous development approach:

```python
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def main():
    # Custom configuration
    config = ConfigManager(
        provider='deepseek',
        deepseek_model='deepseek-chat',
        max_iterations=5
    )
    
    # Create Agent
    agent = Agent(config=config, name='my_agent')
    
    # Manually add tools
    agent.add_tool("./tools/weather/weather_mcp.py", "forecast_tool")
    
    # Initialize and use
    await agent.initialize()
    result = await agent.process_query("Your query")
    await agent.shutdown()
```

### ToolTemplate Base Class

FractFlow's core base class providing unified tool development framework:

```python
class ToolTemplate:
    """FractFlow tool template base class"""
    
    # Required attributes
    SYSTEM_PROMPT: str      # Agent system prompt
    TOOL_DESCRIPTION: str   # Tool functionality description
    
    # Optional attributes
    TOOLS: List[Tuple[str, str]] = []        # Dependent tools list
    MCP_SERVER_NAME: Optional[str] = None    # MCP server name
    
    # Core methods
    @classmethod
    def create_config(cls) -> ConfigManager:
        """Create configuration - can be overridden"""
        pass
    
    @classmethod
    async def create_agent(cls) -> Agent:
        """Create agent instance"""
        pass
    
    @classmethod
    def main(cls):
        """Main entry point - supports three running modes"""
        pass
```

#### Key Attribute Details

**Important Role of TOOL_DESCRIPTION**:

In FractFlow's fractal intelligence architecture, `TOOL_DESCRIPTION` is not just documentation for developers, but more importantly:

- **Reference manual for upper-layer Agents**: When a composite tool (like visual_article_agent) calls lower-layer tools, the upper-layer Agent reads the lower-layer tool's TOOL_DESCRIPTION to understand how to use it correctly
- **Tool interface specification**: Defines input parameter formats, return value structures, usage scenarios, etc.
- **Basis for intelligent calling**: Upper-layer Agents determine when and how to call specific tools based on this description

**Example**: When visual_article_agent calls file_io tool:
```python
# Upper-layer Agent reads file_io tool's TOOL_DESCRIPTION
# Then constructs call requests based on parameter formats described
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
```

Therefore, writing clear and accurate TOOL_DESCRIPTION is crucial for the correct operation of fractal intelligence. However, TOOL_DESCRIPTION should not be too long.

**SYSTEM_PROMPT Writing Guidelines**:

Unlike TOOL_DESCRIPTION which faces upper-layer Agents, `SYSTEM_PROMPT` is the internal behavior instruction for the current Agent. Reference visual_article_agent's practice:

**Structured Design**:
```python
# Reference: tools/composite/visual_article_agent.py
SYSTEM_PROMPT = """
【Strict Constraints】
❌ Absolutely Forbidden: Direct content output
✅ Must Execute: Complete tasks through tool calls

【Workflow】
1. Analyze requirements
2. Call related tools
3. Verify results
"""
```

**Key Techniques**:
- **Clear Prohibitions**: Use `❌` to define what cannot be done, avoiding common errors
- **Forced Execution**: Use `✅` to specify required behavior patterns
- **Process-oriented**: Break complex tasks into clear steps
- **Verification Mechanism**: Require confirmation of results after each step

This design ensures consistency and predictability of Agent behavior, which is key to reliable operation of composite tools.

### Configuration Management

```python
from FractFlow.infra.config import ConfigManager

# Basic configuration
config = ConfigManager()

# Custom configuration
config = ConfigManager(
    provider='openai',              # Model provider: openai/anthropic/deepseek
    openai_model='gpt-4',          # Specific model
    max_iterations=20,             # Maximum iterations
    temperature=0.7,               # Generation temperature
    custom_system_prompt="...",    # Custom system prompt
    tool_calling_version='stable', # Tool calling version: stable/turbo
    timeout=120                    # Timeout setting
)
```

## File Organization
```
tools/
├── core/                 # Core tools
│   └── your_tool/
│       ├── your_tool_agent.py    # Main agent
│       ├── your_tool_mcp.py      # MCP tool implementation
│       └── __init__.py
└── composite/            # Composite tools
    └── your_composite_tool.py
```
#### Naming Conventions
- File names: `snake_case`
- Class names: `PascalCase`

## Recent Updates

### Web UI Tool Description Enhancement (2025-01-20)

Enhanced the web UI to display complete tool descriptions instead of truncating them at 120 characters. 

**Features Added:**
- Expand/collapse mechanism for tool descriptions
- Smooth animations using framer-motion
- Responsive design that adapts to different screen sizes
- Visual indicators for expandable content
- Maintains original card layout when content is short

**Technical Implementation:**
- Added state management to AgentCard component
- Integrated framer-motion animations for smooth transitions
- Enhanced CSS styling with proper expand button design
- Ensured compatibility with existing interaction logic
- Added proper event handling to prevent conflicts

This enhancement allows users to access complete tool documentation while maintaining a clean interface, supporting FractFlow's philosophy of providing comprehensive information for intelligent decision-making.

## Getting Started

[Rest of existing README content...]
