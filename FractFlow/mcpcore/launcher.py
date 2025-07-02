"""
MCP launcher implementation.

Provides functionality to manage and launch multiple MCP tool servers.
"""

import os
from typing import Dict, List, Optional, Any

from .client_pool import get_client_pool
from ..infra.config import ConfigManager
from ..infra.logging_utils import get_logger

class MCPLauncher:
    """
    Manages and launches multiple MCP tool servers.
    
    Provides a unified interface to access all available tools.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the MCP launcher.
        
        Args:
            config: Configuration manager instance to use
        """
        self.config = config or ConfigManager()
        
        # Push component name to call path
        self.config.push_to_call_path("launcher")
        
        # Initialize logger
        self.logger = get_logger(self.config.get_call_path())
        
        self.client_pool = get_client_pool()
        self.server_paths: Dict[str, str] = {}
        self.http_servers: Dict[str, Dict[str, Any]] = {}
        self.http_urls: Dict[str, str] = {}  # Remote HTTP URLs
        
        self.logger.debug("Launcher initialized")
        
    def register_server(self, server_name: str, server_info) -> None:
        """
        Register an MCP server to be launched with support for stdio, HTTP, and remote URL modes.
        
        Args:
            server_name: A unique name for this server
            server_info: Script path (stdio), dict with transport config (HTTP), or dict with HTTP URL
            
        Raises:
            FileNotFoundError: If the server script doesn't exist
        """
        if isinstance(server_info, dict):
            if 'type' in server_info and server_info['type'] == 'http_url':
                # Remote HTTP URL
                self.http_urls[server_name] = server_info['url']
                self.logger.debug(f"Registered remote HTTP URL", {"name": server_name, "url": server_info['url']})
            else:
                # Local HTTP server config
                self.http_servers[server_name] = server_info
                self.logger.debug(f"Registered HTTP server", {"name": server_name, "config": server_info})
        else:
            # Local script path
            if not os.path.exists(server_info):
                error_msg = f"Server script not found: {server_info}"
                self.logger.error(error_msg, {"server": server_name, "path": server_info})
                raise FileNotFoundError(error_msg)
            self.server_paths[server_name] = server_info
            self.logger.debug(f"Registered stdio server", {"name": server_name, "path": server_info})
        
    async def launch_all(self) -> None:
        """
        Launch all registered MCP servers (stdio, HTTP, and remote URLs) and connect clients.
        
        Raises:
            Exception: If any server fails to launch
        """
        total_servers = len(self.server_paths) + len(self.http_servers) + len(self.http_urls)
        self.logger.debug(f"Launching servers", {
            "stdio_count": len(self.server_paths), 
            "http_count": len(self.http_servers),
            "url_count": len(self.http_urls),
            "total": total_servers
        })
        
        # Launch stdio servers
        for server_name, script_path in self.server_paths.items():
            self.logger.debug(f"Launching stdio server", {"name": server_name})
            await self.client_pool.add_client(server_name, script_path)
        
        # Launch HTTP servers
        for server_name, config in self.http_servers.items():
            self.logger.debug(f"Launching HTTP server", {"name": server_name})
            await self.client_pool.add_client(server_name, config)
        
        # Connect to remote HTTP URLs
        for server_name, url in self.http_urls.items():
            self.logger.debug(f"Connecting to remote HTTP URL", {"name": server_name, "url": url})
            await self.client_pool.add_http_url_client(server_name, url)
            
        self.logger.info("All servers launched successfully")
        
    async def shutdown(self) -> None:
        """
        Shutdown all MCP servers and clients.
        
        Raises:
            Exception: If shutdown fails
        """
        try:
            self.logger.debug("Shutting down servers")
            await self.client_pool.cleanup()
            self.logger.info("All servers and clients shut down")
        except Exception as e:
            self.logger.error(f"Error shutting down servers", {"error": str(e)})
            raise 