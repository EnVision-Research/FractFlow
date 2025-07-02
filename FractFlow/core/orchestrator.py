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
from typing import Dict, List, Any, Optional

from FractFlow.models.factory import create_model
from FractFlow.models.base_model import BaseModel
from FractFlow.infra.config import ConfigManager
from FractFlow.infra.error_handling import AgentError, handle_error, ConfigurationError
from FractFlow.infra.logging_utils import get_logger

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
                          Example: {'weather': '/path/to/weather_agent.py',
                                   'search': '/path/to/search_tool.py'}
            provider: The AI provider to use (e.g., 'openai', 'deepseek')
            config: Configuration manager instance to use
        """
        # Create or use the provided config
        if config is None:
            self.config = ConfigManager()
        else:
            self.config = config
        
        # Push component name to call path
        self.config.push_to_call_path("orchestrator")
        
        # Initialize logger
        self.logger = get_logger(self.config.get_call_path())
        
        # Get provider from config or use provided override
        self.provider = provider or self.config.get('agent.provider', 'openai')
        
        # Create the model directly using factory with provider only
        self.model = create_model(provider=self.provider, config=self.config)
        
        # Tool launcher will be initialized in self.start()
        self.launcher = None
        self.tool_loader = None
        
        # Register tools if provided
        self.tool_configs = tool_configs or {}
        
        self.logger.debug("Orchestrator initialized", {"provider": self.provider, "tools_count": len(self.tool_configs)})
        
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
            self.logger.debug(f"Queued tool provider registration", {"name": name})
            return
            
        self.launcher.register_server(name, provider_info)
        self.logger.debug(f"Registered tool provider", {"name": name})
        
    def register_tools_from_config(self, tools_config: Dict[str, Any]) -> None:
        """
        Register multiple tool providers from a configuration dictionary.
        
        Args:
            tools_config: Dictionary mapping tool names to their provider scripts or HTTP URL configs
                          Example: {'weather': '/path/to/weather_agent.py',
                                   'search': {'type': 'http_url', 'url': 'http://...'},
                                   'file': '/path/to/file_tool.py'}
        """
        for tool_name, config_info in tools_config.items():
            # Handle HTTP URL dictionary format
            if isinstance(config_info, dict) and config_info.get('type') == 'http_url':
                self.register_tool_provider(tool_name, config_info)
                self.logger.debug(f"Registered HTTP tool provider", {"name": tool_name, "url": config_info.get('url')})
            # Handle string path format
            elif isinstance(config_info, str):
                if os.path.exists(config_info):
                    self.register_tool_provider(tool_name, config_info)
                    self.logger.debug(f"Registered tool provider", {"name": tool_name, "path": config_info})
                else:
                    self.logger.warning(f"Tool script not found", {"name": tool_name, "path": config_info})
            else:
                self.logger.warning(f"Invalid tool configuration format", {"name": tool_name, "config": config_info})
                
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
                self.logger.warning(f"Tools configuration file not found", {"path": config_file_path})
                return
                
            with open(config_file_path, 'r') as f:
                config_data = json.load(f)
                
            if "tools" in config_data and isinstance(config_data["tools"], dict):
                self.register_tools_from_config(config_data["tools"])
                self.logger.info(f"Registered tools from file", {"path": config_file_path, "count": len(config_data["tools"])})
            else:
                self.logger.warning(f"Invalid tools configuration format", {"path": config_file_path})
        except Exception as e:
            error = handle_error(e, {"config_file": config_file_path})
            self.logger.error(f"Error loading tools configuration", {"error": str(error), "path": config_file_path})
        
    async def start(self) -> None:
        """Initialize and launch the agent system."""
        # Import here to avoid circular imports
        from FractFlow.mcpcore.launcher import MCPLauncher
        from FractFlow.mcpcore.tool_loader import MCPToolLoader
        
        self.logger.debug("Starting orchestrator")
        
        # Initialize MCP components
        self.launcher = MCPLauncher()
        self.tool_loader = MCPToolLoader()
        
        # Register tools from config
        if self.tool_configs:
            self.register_tools_from_config(self.tool_configs)
            
        # Launch all registered tool providers
        self.logger.debug("Launching tool providers")
        await self.launcher.launch_all()
        self.logger.debug("Orchestrator started")
        
    async def shutdown(self) -> None:
        """Shut down the agent system."""
        if self.launcher:
            self.logger.debug("Shutting down orchestrator")
            await self.launcher.shutdown()
            self.logger.debug("Orchestrator shut down")
        
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
                    self.logger.debug(f"Loaded tools from client", {"client": client_name, "count": len(client_tools)})
                except Exception as e:
                    self.logger.error(f"Error loading tools from client", {"client": client_name, "error": str(e)})
            
            self.logger.debug(f"Total tools loaded", {"count": len(all_tools)})
            return all_tools
        except Exception as e:
            error = handle_error(e)
            self.logger.error(f"Error getting available tools", {"error": str(error)})
            return []
            
    async def get_tool_name_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping from user-defined tool names to actual function names.
        
        Returns:
            Dictionary mapping tool names to lists of function names
            Example: {'file_manager_agent': ['fileiotool'], 'image_creator_agent': ['create_image_with_gpt', 'edit_image_with_gpt']}
        """
        if not self.launcher or not self.tool_loader:
            self.logger.warning("Orchestrator not started, returning empty mapping")
            return {}
            
        mapping = {}
        
        try:
            # For each configured tool, get the functions it provides
            for tool_name, tool_path in self.tool_configs.items():
                # Find the client for this tool
                if tool_name in self.launcher.client_pool.clients:
                    session = self.launcher.client_pool.clients[tool_name]
                    try:
                        response = await session.list_tools()
                        function_names = [tool.name for tool in response.tools]
                        mapping[tool_name] = function_names
                        self.logger.debug(f"Mapped tool", {"tool_name": tool_name, "functions": function_names})
                    except Exception as e:
                        self.logger.error(f"Error getting functions for tool", {"tool_name": tool_name, "error": str(e)})
                        mapping[tool_name] = []
                else:
                    self.logger.warning(f"No client found for tool", {"tool_name": tool_name})
                    mapping[tool_name] = []
                    
        except Exception as e:
            error = handle_error(e)
            self.logger.error(f"Error creating tool name mapping", {"error": str(error)})
            
        return mapping

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