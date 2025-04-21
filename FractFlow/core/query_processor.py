"""
query_processor.py
Author: Ying-Cong Chen (yingcong.ian.chen@gmail.com)
Date: 2025-04-08
Description: Processes user queries, manages model execution, and handles the loop with tool calls.
License: MIT License
"""

"""
Query processor.

Handles the processing of user queries, manages model execution,
and processes model responses with tool calls.
"""

import logging
from typing import Dict, Any, Optional, List
from .orchestrator import Orchestrator
from .tool_executor import ToolExecutor
from ..infra.config import ConfigManager
from ..infra.error_handling import AgentError, handle_error
from ..infra.logging_utils import get_logger

logger = get_logger(__name__)

class QueryProcessor:
    """
    Processes user queries and manages the loop.
    
    Handles the interaction between the user's query, the model, and tools,
    implementing the core loop.
    """
    
    def __init__(self, orchestrator: Orchestrator, tool_executor: ToolExecutor, config: Optional[ConfigManager] = None):
        """
        Initialize the query processor.
        
        Args:
            orchestrator: The orchestrator that manages components
            tool_executor: The tool executor that handles tool execution
            config: Configuration manager instance to use
        """
        self.orchestrator = orchestrator
        self.tool_executor = tool_executor
        self.config = config or ConfigManager()
        self.max_iterations = self.config.get('agent.max_iterations', 10)
    
    async def process_query(self, user_query: str) -> str:
        """
        Process a user query through the loop.
        
        Args:
            user_query: The user's input query
            
        Returns:
            The final response to the user
        """
        try:
            model = self.orchestrator.get_model()
            
            # Add user message to history
            logger.debug("Processing user query", {"query": user_query})
            model.add_user_message(user_query)
            
            # Get the tools schema
            tools = await self.orchestrator.get_available_tools()
            
            # Initial content placeholder
            content = ""
            
            # Main agent loop
            for iteration in range(self.max_iterations):
                logger.debug("Starting iteration", {"current": iteration+1, "max": self.max_iterations})
                
                # Get response from model
                response = await model.execute(tools)
                
                message = response["choices"][0]["message"]
                tool_calls = message.get("tool_calls", [])
                content = message.get("content", "Sorry, I couldn't understand your request.")
                
                # Log reasoning content (if exists)
                reasoning_content = message.get("reasoning_content")
                if reasoning_content:
                    logger.debug("Reasoning content", {"reasoning": reasoning_content})
                
                # If there are no tool calls, return final answer
                if not tool_calls:
                    # Add final answer to conversation history
                    model.add_assistant_message(content)
                    # Log complete conversation history for final result
                    model.history.log_history(logging.INFO, f"Interation History（Number of Iteration:{iteration+1}）")
                    return content
                
                # Process all tool calls in each iteration
                if tool_calls and len(tool_calls) > 0:
                    # Store the assistant message first with all tool calls
                    model.add_assistant_message(content, tool_calls)
                    
                    # Process each tool call
                    for tool_call in tool_calls:
                        # Skip None values
                        if tool_call is None:
                            logger.warning("Received empty tool call")
                            continue
                            
                        # Extract tool information in OpenAI format
                        function_info = tool_call["function"]
                        tool_name = function_info.get("name")
                        
                        # Arguments might be a JSON string, so parse it if needed
                        function_args = function_info.get("arguments", "{}")
                        if isinstance(function_args, str):
                            import json
                            try:
                                function_args = json.loads(function_args)
                            except json.JSONDecodeError:
                                function_args = {}
                        
                        tool_call_id = tool_call.get("id", "unknown")
                        
                        if not tool_name:
                            logger.warning("Tool call missing 'name' field")
                            continue
                        
                        logger.debug("Calling tool", {"name": tool_name, "args": function_args})
                        
                        # Call the tool
                        try:
                            result = await self.tool_executor.execute_tool(tool_name, function_args)
                            # Add tool execution result log
                            logger.debug("Tool execution result", {"tool": tool_name, "result": result})
                            # Add result to conversation history
                            model.add_tool_result(tool_name, result, tool_call_id)
                                
                        except Exception as e:
                            error = handle_error(e, {"tool_name": tool_name, "args": function_args})
                            error_message = f"Error calling tool {tool_name}: {str(error)}"
                            logger.error(error_message, {"tool": tool_name, "error": str(error)})
                            model.add_tool_result(tool_name, error_message, tool_call_id)
            
            # If we reached the maximum iterations, return a fallback response
            logger.warning("Reached maximum iterations", {"max": self.max_iterations})
            # Log complete conversation history when max iterations reached
            final_content = "I spent too much time processing your request. Here's what I've gathered so far: " + content
            model.add_assistant_message(final_content)
            model.history.log_history(logging.WARNING, "Maximum iteration count reached")
            return final_content
        
        except Exception as e:
            error = handle_error(e, {"user_query": user_query})
            logger.error("Error in process_query", {"error": str(error)})
            # If model is initialized, log conversation history when error occurs
            if 'model' in locals() and hasattr(model, 'history'):
                model.history.log_history(logging.ERROR, "ERROR in process_query")
            return f"Sorry, there was a technical problem processing your request. Error: {str(error)}"

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history from the current model.
        
        Returns:
            The current conversation history
        """
        return self.orchestrator.get_history() 