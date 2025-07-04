"""
tool_template.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-05-31
Description: Base template class for creating FractFlow tools that can run in multiple modes.
License: MIT License
"""


import asyncio
import os
import sys
import logging
import argparse
from typing import List, Tuple, Dict, Any, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import os.path as osp
import socket

# Import the FractFlow Agent and Config
from .agent import Agent
from .infra.config import ConfigManager
from .infra.logging_utils import setup_logging, get_logger

class ToolTemplate:
    """
    Base template class for creating FractFlow tools with multiple running modes.
    
    This template is designed as both a working base class and a learning example
    for creating FractFlow tools. It supports three levels of customization:
    
    ===== SCENARIO 1: Minimal Setup (Most Common) =====
    Simply inherit and define two required attributes:
    
        class MyTool(ToolTemplate):
            SYSTEM_PROMPT = "You are a helpful assistant for..."
            TOOL_DESCRIPTION = "This tool helps users with..."
    
    ===== SCENARIO 2: Custom Tools =====
    Add custom tool configuration:
    
        class MyTool(ToolTemplate):
            SYSTEM_PROMPT = "You are a helpful assistant for..."
            TOOL_DESCRIPTION = "This tool helps users with..."
            TOOLS = [("path/to/my_tool.py", "my_tool_name")]
    
    The tool names you specify in TOOLS (e.g., "my_tool_name") can be 
    directly referenced in your SYSTEM_PROMPT. The system will automatically map these 
    names to the actual function names that the tool scripts provide.
    
    Example:
        TOOLS = [("../file_io/file_io_agent.py", "file_manager_agent")]
        SYSTEM_PROMPT = '''
        When user needs file operations, use file_manager_agent.
        '''
    
    The system will automatically inform the model that "file_manager_agent" maps to 
    the actual functions provided by file_io_agent.py (like "fileioagent").
    
    ===== SCENARIO 3: Advanced Configuration =====
    Override configuration method for complex setups:
    
        class MyTool(ToolTemplate):
            SYSTEM_PROMPT = "You are a helpful assistant for..."
            TOOL_DESCRIPTION = "This tool helps users with..."
            TOOLS = [("path/to/my_tool.py", "my_tool_name")]
            
            @classmethod
            def create_config(cls):
                return ConfigManager(
                    provider='openai',
                    openai_model='gpt-4',
                    max_iterations=20,
                    custom_system_prompt=cls.SYSTEM_PROMPT
                )
    
    ===== REQUIRED ATTRIBUTES =====
    SYSTEM_PROMPT (str): The system prompt for the agent
    TOOL_DESCRIPTION (str): Description for the main MCP tool function
    
    ===== OPTIONAL ATTRIBUTES =====
    TOOLS (List[Tuple[str, str]]): List of (tool_path, tool_name) tuples
    MCP_SERVER_NAME (str): Custom MCP server name (defaults to class name)
    
    ===== OPTIONAL: HTTP Transport Configuration =====
    For HTTP mode, simply run with: python your_tool.py --http-port 8080
    All other HTTP settings are automatically configured:
    - Host: 0.0.0.0 (allows external access)
    - Path: /{class_name} (semantic endpoint)
    
    ===== OPTIONAL OVERRIDES =====
    create_config() -> ConfigManager: Custom configuration creation
    
    ===== CRITICAL: SYSTEM_PROMPT & TOOL_DESCRIPTION ALIGNMENT =====
    
    **IMPORTANT**: These tools are essentially "GPT agents with tools" that can only 
    output strings. However, through SYSTEM_PROMPT conventions, they can output 
    various structured information formats.
    
    SYSTEM_PROMPT and TOOL_DESCRIPTION must be aligned:
    
    1. **Tool Nature Understanding**:
       - Your tool is a GPT agent that outputs strings
       - TOOL_DESCRIPTION describes what the string output contains
       - SYSTEM_PROMPT guides how to format that string output
    
    2. **Output Format Consistency**:
       - If TOOL_DESCRIPTION promises structured data (e.g., JSON-like fields),
         SYSTEM_PROMPT must instruct the agent to format output accordingly
       - Example TOOL_DESCRIPTION: "Returns: 'result': operation result, 'success': boolean"
         Matching SYSTEM_PROMPT: "Format your response with: result: [description], success: [true/false]"
    
    3. **Common Mistakes to Avoid**:
       - TOOL_DESCRIPTION claiming to return actual JSON objects (it's strings!)
       - SYSTEM_PROMPT with casual tone while TOOL_DESCRIPTION promises formal output
       - Missing output format guidance in SYSTEM_PROMPT
       - Contradictory behavior instructions (e.g., "don't output" vs "return structured data")
    
    4. **Best Practices**:
       - Always include output format requirements in SYSTEM_PROMPT
       - Make TOOL_DESCRIPTION describe the string content structure
       - Keep both professional and consistent in tone
       - Test that actual outputs match TOOL_DESCRIPTION promises
    
    5. **Example of Good Alignment**:
    
        TOOL_DESCRIPTION = '''
        Processes text files and returns operation results.
        
        Returns:
        - operation_result: Description of what was performed
        - file_content: Relevant file content (if reading)
        - success: Boolean indicating completion
        - message: Additional context about the operation
        '''
        
        SYSTEM_PROMPT = '''
        You are a file processing assistant.
        
        # Output Format Requirements
        Your response should contain:
        - operation_result: [describe what you did]
        - file_content: [show relevant content when reading]
        - success: [true/false]
        - message: [any additional notes]
        '''
    """
    
    # ===== REQUIRED: User must define these =====
    SYSTEM_PROMPT: str = None
    TOOL_DESCRIPTION: str = None
    
    # ===== OPTIONAL: User can define these =====
    TOOLS: List[Tuple[str, str]] = []
    MCP_SERVER_NAME: Optional[str] = None
    
    # ===== OPTIONAL: HTTP Transport Configuration =====
    TRANSPORT_MODE: Optional[str] = "stdio"  # "stdio" | "http"
    HTTP_PORT: Optional[int] = None
    HTTP_HOST: Optional[str] = "0.0.0.0"  # Allow external access by default
    HTTP_PATH: Optional[str] = None  # Will be set to /{class_name} automatically
    
    # ===== INTERNAL: Template implementation =====
    # Class-level MCP server instance
    _mcp = None
    
    @classmethod
    def _create_fastmcp_server(cls) -> FastMCP:
        """
        Create FastMCP server instance without running it.
        
        This method is used by AgentLauncher to create server instances
        that can be mounted to a shared FastAPI application.
        
        Returns:
            FastMCP: Configured FastMCP server instance ready for mounting
        """
        if cls._mcp is None:
            cls._mcp = FastMCP(cls._get_mcp_server_name())
            tool_name = f"{cls.__name__.lower()}"
            tool_description = cls._get_tool_description()
            cls._mcp.tool(name=tool_name, description=tool_description)(cls._mcp_tool_function)
        return cls._mcp
    
    @classmethod
    def create_config(cls) -> ConfigManager:
        """
        Create configuration for the agent.
        
        **SCENARIO 3 USER OVERRIDE POINT**
        Override this method to customize model provider, parameters, and behavior.
        Most users won't need to override this - the defaults work well.
        
        Default configuration:
        - Provider: DeepSeek
        - Model: deepseek-chat  
        - Max iterations: 5
        - Tool calling: turbo mode
        
        Returns:
            ConfigManager: Configured instance ready for Agent creation
            
        Example override:
            @classmethod
            def create_config(cls):
                return ConfigManager(
                    provider='openai',
                    openai_model='gpt-4',
                    max_iterations=20,
                    custom_system_prompt=cls.SYSTEM_PROMPT
                )
        """
        return ConfigManager(custom_system_prompt=cls.SYSTEM_PROMPT)
    
    @classmethod
    async def create_agent(cls, name_suffix='assistant') -> Agent:
        """
        Create and initialize an Agent with tools.
        
        Args:
            name_suffix: Suffix for agent name (e.g., 'assistant', 'agent')
            
        Returns:
            Agent: Initialized agent ready for use
        """
        config = cls.create_config()
        agent = Agent(config=config, name=f'{cls.__name__.lower()}_{name_suffix}')
        
        # Add tools to the agent
        await cls._add_tools_to_agent(agent)
        
        # Initialize the agent
        print("Initializing agent...")
        await agent.initialize()
        
        return agent
    
    @classmethod
    async def _add_tools_to_agent(cls, agent: Agent):
        """
        Add tools to the agent based on TOOLS configuration.
        
        Args:
            agent: Agent instance to add tools to
        """
        project_root = cls._get_project_root()

        for tool_path, tool_name in cls.TOOLS:
            # Handle HTTP URLs directly
            if tool_path.startswith(('http://', 'https://')):
                agent.add_tool(tool_path, tool_name)
                continue
                
            # Handle relative paths - now relative to project root
            if not os.path.isabs(tool_path):
                full_path = os.path.join(project_root, tool_path)
            else:
                full_path = tool_path
                
            if not os.path.exists(full_path):
                raise ValueError(f"Tool path does not exist: {full_path}")
                
            agent.add_tool(full_path, tool_name)
    
    @classmethod
    def _get_project_root(cls):
        """
        Find the project root directory by looking for characteristic files.
        
        Returns:
            str: Path to the project root directory
            
        Raises:
            ValueError: If project root cannot be found
        """
        current_file = os.path.abspath(sys.modules[cls.__module__].__file__)
        current_dir = os.path.dirname(current_file)
        
        # Characteristic files that indicate project root
        root_indicators = [
            'pyproject.toml',  # 最可靠的项目根标识
            '.git',            # 版本控制根目录
            'setup.py'         # Python包根目录
        ]
        
        # Search upwards from current directory
        search_dir = current_dir
        while search_dir != os.path.dirname(search_dir):  # Not at filesystem root
            for indicator in root_indicators:
                if os.path.exists(os.path.join(search_dir, indicator)):
                    return search_dir
            search_dir = os.path.dirname(search_dir)
        
        # If we can't find project root, fall back to current directory
        # and issue a warning
        import warnings
        warnings.warn(
            f"Could not find project root from {current_file}. "
            f"Using current directory as fallback: {current_dir}",
            UserWarning
        )
        return current_dir

    @classmethod
    def _get_mcp_server_name(cls):
        """Get the MCP server name, using class name as default"""
        return cls.MCP_SERVER_NAME or f"{cls.__name__.lower()}_tool"
    
    @classmethod
    def _get_tool_description(cls):
        """Get the tool description for MCP function"""
        if cls.TOOL_DESCRIPTION:
            return cls.TOOL_DESCRIPTION
        
        return f"""
        Performs intelligent operations based on natural language requests using {cls.__name__}.
        
        Parameters:
            query: str - Natural language description of operation to perform
        
        Returns:
            str - Operation result or error message with guidance
        """
    
    @classmethod
    def _get_transport_config(cls) -> Dict[str, Any]:
        """Get transport configuration from class attributes"""
        # Auto-generate HTTP path based on class name if not set
        http_path = cls.HTTP_PATH or f"/{cls.__name__.lower()}"
        
        return {
            'mode': cls.TRANSPORT_MODE,
            'host': cls.HTTP_HOST,
            'port': cls.HTTP_PORT or cls._get_available_port(),
            'path': http_path
        }
    
    @classmethod
    def _get_available_port(cls, preferred_port: Optional[int] = None) -> int:
        """Get an available port for HTTP server"""
        if preferred_port:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', preferred_port))
                    return preferred_port
                except OSError:
                    pass
        
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    @classmethod
    def _get_local_ip(cls):
        """Get the local IP address for display purposes"""
        import socket
        try:
            # Connect to a remote address to determine the local IP
            # This doesn't actually send data, just determines routing
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            # Fallback to localhost if unable to determine IP
            return "127.0.0.1"
    
    @classmethod
    def _run_http_server(cls):
        """Run server using HTTP transport"""
        if cls._mcp is None:
            cls._mcp = FastMCP(cls._get_mcp_server_name())
            tool_name = f"{cls.__name__.lower()}"
            tool_description = cls._get_tool_description()
            cls._mcp.tool(name=tool_name, description=tool_description)(cls._mcp_tool_function)
        
        config = cls._get_transport_config()
        
        # Configure host, port and path in FastMCP settings
        cls._mcp.settings.host = config['host']
        cls._mcp.settings.port = config['port']
        cls._mcp.settings.streamable_http_path = config['path']
        
        # Display user-friendly access URLs
        if config['host'] == '0.0.0.0':
            # Show both localhost and actual IP when binding to all interfaces
            local_ip = cls._get_local_ip()
            print(f"Starting {cls.__name__} HTTP server:")
            print(f"  📱 Local access:  http://127.0.0.1:{config['port']}{config['path']}")
            print(f"  🌐 Network access: http://{local_ip}:{config['port']}{config['path']}")
        else:
            # Show the specific host when binding to specific interface
            full_url = f"http://{config['host']}:{config['port']}{config['path']}"
            print(f"Starting {cls.__name__} HTTP server at {full_url}")
        
        # Use streamable-http transport (correct parameter for MCP 1.x)
        cls._mcp.run(transport='streamable-http')
    
    @classmethod
    def _run_stdio_server(cls):
        """Run server using STDIO transport (original behavior)"""
        if cls._mcp is None:
            cls._mcp = FastMCP(cls._get_mcp_server_name())
            tool_name = f"{cls.__name__.lower()}"
            tool_description = cls._get_tool_description()
            cls._mcp.tool(name=tool_name, description=tool_description)(cls._mcp_tool_function)
        
        cls._mcp.run(transport='stdio')
    
    @classmethod
    def _validate_configuration(cls):
        """Validate that required class attributes are defined"""
        if cls.SYSTEM_PROMPT is None:
            raise ValueError(
                f"{cls.__name__} must define SYSTEM_PROMPT. "
                f"Example: SYSTEM_PROMPT = 'You are a helpful assistant for...'"
            )
        
        if cls.TOOL_DESCRIPTION is None:
            raise ValueError(
                f"{cls.__name__} must define TOOL_DESCRIPTION. "
                f"Example: TOOL_DESCRIPTION = 'This tool helps users with...'"
            )
        
        if not cls.TOOLS:
            # This is actually optional, so make it a warning in the validation
            # Most tools will have default tools or auto-discovery
            pass
        
        # Validate tool paths exist
        project_root = cls._get_project_root()
        print("project_root:", project_root)
        print("Tools: ", cls.TOOLS)
        for tool_path, tool_name in cls.TOOLS:
            # Skip validation for HTTP URLs
            if tool_path.startswith(('http://', 'https://')):
                continue
                
            # Handle relative paths - now relative to project root
            if not os.path.isabs(tool_path):
                full_path = os.path.join(project_root, tool_path)
            else:
                full_path = tool_path
                
            if not os.path.exists(full_path):
                raise ValueError(
                    f"Tool path does not exist: {full_path}\n"
                    f"Check the TOOLS configuration in {cls.__name__}.\n"
                    f"Tool paths should be relative to the project root, absolute paths, or HTTP URLs.\n"
                    f"Project root detected: {project_root}"
                )
    
    @classmethod
    async def _mcp_tool_function(cls, query: str) -> str:
        """The main MCP tool function that processes queries"""
        agent = await cls.create_agent()
        try:
            result = await agent.process_query(query)
            return result
        finally:
            await agent.shutdown()
    
    @classmethod
    async def _run_interactive(cls):
        """Interactive chat mode with multi-turn conversation support"""
        print(f"\n{cls.__name__} Interactive Mode")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
        
        # Set stdin to handle UTF-8 properly
        import sys
        if hasattr(sys.stdin, 'reconfigure'):
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        
        agent = await cls.create_agent('agent')
        
        try:
            while True:
                try:
                    user_input = input("You: ")
                    if user_input.lower() in ('exit', 'quit', 'bye'):
                        break
                    
                    print("\nProcessing...\n")
                    result = await agent.process_query(user_input)
                    print(f"Agent: {result}")
                except UnicodeDecodeError as e:
                    print(f"Input encoding error: {e}")
                    print("Please try again with proper UTF-8 encoding.")
                    continue
                except EOFError:
                    print("\nReceived EOF, ending session.")
                    break
                except KeyboardInterrupt:
                    print("\nReceived interrupt, ending session.")
                    break
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    async def _run_single_query(cls, query: str):
        """One-time execution mode for a single query"""
        print(f"Processing query: {query}")
        print("\nProcessing...\n")
        
        agent = await cls.create_agent('agent')
        
        try:
            result = await agent.process_query(query)
            print(f"Result: {result}")
            return result
        finally:
            await agent.shutdown()
            print("\nAgent session ended.")
    
    @classmethod
    def _run_mcp_server(cls):
        """Run in MCP Server mode with configurable transport"""
        transport_config = cls._get_transport_config()
        
        if transport_config['mode'] == 'http':
            cls._run_http_server()
        else:
            cls._run_stdio_server()
    
    @classmethod
    def main(cls):
        """Main entry point for the tool"""
        # Validate configuration
        cls._validate_configuration()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description=f'{cls.__name__} - Unified Interface')
        parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
        parser.add_argument('--query', '-q', type=str, help='Single query mode: process this query and exit')
        parser.add_argument('--log-level', '-l', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL')
        parser.add_argument('--http-port', type=int, help='Run HTTP server on specified port (enables HTTP mode)')
        args = parser.parse_args()
        
        # Override class attributes with command line arguments
        if args.http_port:
            cls.TRANSPORT_MODE = 'http'
            cls.HTTP_PORT = args.http_port
            # Other HTTP settings (host, path) use class defaults automatically
        
        # Setup logging
        setup_logging(level=args.log_level)
        
        if args.interactive:
            # Interactive mode
            print(f"Starting {cls.__name__} in interactive mode.")
            asyncio.run(cls._run_interactive())
        elif args.query:
            # Single query mode
            print(f"Starting {cls.__name__} in single query mode.")
            asyncio.run(cls._run_single_query(args.query))
        else:
            # Default: MCP Server mode
            print(f"Starting {cls.__name__} in MCP Server mode.")
            cls._run_mcp_server() 