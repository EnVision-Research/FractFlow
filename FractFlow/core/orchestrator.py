"""
orchestrator.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Core orchestrator that handles high-level orchestration of agent components, including model creation, tool management, and system initialization.
License: MIT License
"""

"""
Core orchestrator.

Handles high-level orchestration of the agent components, including model creation,
tool management, and initialization of the agent system.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional

from FractFlow.models.factory import create_model
from FractFlow.models.base_model import BaseModel
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.error_handling import AgentError, handle_error, ConfigurationError

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Manages high-level orchestration of agent components.
    
    Responsible for initializing the agent system, managing model and tool providers,
    and handling the registration and launching of tools.
    """
    
    def __init__(self,
                 tool_configs: Optional[Dict[str, str]] = None,
                 provider: Optional[str] = None,
                 config: Optional[ConfigManager] = None):
        """
        Initialize the orchestrator.
        
        Args:
            tool_configs: Dictionary mapping tool names to their provider scripts
                          Example: {'weather': '/path/to/weather_tool.py',
                                   'search': '/path/to/search_tool.py'}
            provider: The AI provider to use (e.g., 'openai', 'deepseek')
            config: Configuration manager instance to use
        """
        # Create or use the provided config
        self.config = config or ConfigManager()
        
        # Get provider from config or use provided override
        self.provider = provider or self.config.get('agent.provider', 'openai')
        
        # Create the model directly using factory with provider only
        self.model = create_model(provider=self.provider, config=self.config)
        
        # Tool launcher will be initialized in self.start()
        self.launcher = None
        self.tool_loader = None
        
        # Register tools if provided
        self.tool_configs = tool_configs or {}
        
    def register_tool_provider(self, name: str, provider_info: Any) -> None:
        """
        Register a tool provider with the agent.
        
        Args:
            name: Name for the tool provider
            provider_info: Path to the provider script
        """
        if not self.launcher:
            # Store the config until we launch
            self.tool_configs[name] = provider_info
            return
            
        self.launcher.register_server(name, provider_info)
        
    def register_tools_from_config(self, tools_config: Dict[str, str]) -> None:
        """
        Register multiple tool providers from a configuration dictionary.
        
        Args:
            tools_config: Dictionary mapping tool names to their provider scripts
                          Example: {'weather': '/path/to/weather_tool.py',
                                   'search': '/path/to/search_tool.py'}
        """
        for tool_name, script_path in tools_config.items():
            if os.path.exists(script_path):
                self.register_tool_provider(tool_name, script_path)
                logger.debug(f"Registered tool provider: {tool_name} from {script_path}")
            else:
                logger.warning(f"Tool script not found: {script_path} for {tool_name}")
                
    def register_tools_from_file(self, config_file_path: str) -> None:
        """
        Register tool providers from a JSON configuration file.
        
        Args:
            config_file_path: Path to the JSON configuration file
            
        The JSON file should have the format:
        {
            "tools": {
                "tool_name1": "path/to/script1.py",
                "tool_name2": "path/to/script2.py"
            }
        }
        """
        try:
            if not os.path.exists(config_file_path):
                logger.warning(f"Tools configuration file not found: {config_file_path}")
                return
                
            with open(config_file_path, 'r') as f:
                config_data = json.load(f)
                
            if "tools" in config_data and isinstance(config_data["tools"], dict):
                self.register_tools_from_config(config_data["tools"])
            else:
                logger.warning(f"Invalid tools configuration format in {config_file_path}")
        except Exception as e:
            error = handle_error(e, {"config_file": config_file_path})
            logger.error(f"Error loading tools configuration: {error}")
        
    async def start(self) -> None:
        """Initialize and launch the agent system."""
        # Import here to avoid circular imports
        from FractFlow.mcpcore.launcher import MCPLauncher
        from FractFlow.mcpcore.tool_loader import MCPToolLoader
        
        # Initialize MCP components
        self.launcher = MCPLauncher()
        self.tool_loader = MCPToolLoader()
        
        # Register tools from config
        if self.tool_configs:
            self.register_tools_from_config(self.tool_configs)
            
        # Launch all registered tool providers
        await self.launcher.launch_all()
        
    async def shutdown(self) -> None:
        """Shut down the agent system."""
        if self.launcher:
            await self.launcher.shutdown()
        
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools from the registered providers.
        
        Returns:
            List of available tools
        """
        if not self.launcher or not self.tool_loader:
            raise ConfigurationError("Orchestrator not started")
            
        try:
            # Get tools from all clients, not just the first one
            all_tools = []
            for client_name, session in self.launcher.client_pool.clients.items():
                try:
                    client_tools = await self.tool_loader.load_tools(session)
                    all_tools.extend(client_tools)
                    logger.debug(f"Loaded {len(client_tools)} tools from client {client_name}")
                except Exception as e:
                    logger.error(f"Error loading tools from client {client_name}: {e}")
            
            logger.debug(f"Loaded a total of {len(all_tools)} tools")
            return all_tools
        except Exception as e:
            error = handle_error(e)
            logger.error(f"Error getting available tools: {error}")
            return []
            
    def get_model(self) -> BaseModel:
        """
        Get the model instance.
        
        Returns:
            The current model instance
        """
        return self.model 
        
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history from the model.
        
        Returns:
            The current conversation history
        """
        if not self.model:
            return []
        return self.model.history.get_messages() 