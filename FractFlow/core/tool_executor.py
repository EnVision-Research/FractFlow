"""
tool_executor.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Handles the execution of tools based on model requests, providing abstraction between the model and actual tools.
License: MIT License
"""

"""
Tool executor.

Handles the execution of tools based on model requests.
"""

import logging
from typing import Dict, Any, Optional
from ..infra.config import ConfigManager
from ..infra.error_handling import ToolExecutionError, handle_error

logger = logging.getLogger(__name__)

class ToolExecutor:
    """
    Executes tools based on model requests.
    
    Provides a layer of abstraction between the model and the actual tools,
    handling errors and formatting results.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the tool executor.
        
        Args:
            config: Configuration manager instance to use
        """
        self.config = config or ConfigManager()
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool
            
        Returns:
            The result of the tool execution as a string
            
        Raises:
            ToolExecutionError: If the tool execution fails
        """
        try:
            # Get the client pool from the MCP module
            # This is imported here to avoid circular imports
            from ..mcpcore import get_client_pool
            
            # Call the tool using the MCP client pool
            client_pool = get_client_pool()
            result = await client_pool.call(tool_name, arguments)
            return result
            
        except Exception as e:
            error = handle_error(e, {"tool_name": tool_name, "arguments": arguments})
            logger.error(f"Error executing tool {tool_name}: {error}")
            raise ToolExecutionError(f"Failed to execute tool {tool_name}: {str(error)}", e) 