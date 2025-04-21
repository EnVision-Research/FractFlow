"""
DeepSeek model implementation (V2).

Provides implementation of the BaseModel interface for DeepSeek models with native tool calling support.
"""

import json
import logging
import re
import uuid
from typing import Dict, List, Any, Optional
from openai import OpenAI

from .base_model import BaseModel
from ..infra.config import ConfigManager
from ..infra.error_handling import LLMError, handle_error, create_error_response
from ..conversation.base_history import ConversationHistory
from ..conversation.provider_adapters.deepseek_adapter import DeepSeekHistoryAdapter

logger = logging.getLogger(__name__)
config = ConfigManager()

# Define the tool calling instructions as a constant
TOOL_CALLING_INSTRUCTIONS = """When you need to use tools, identify the appropriate tool and provide the required parameters.
You will receive tool responses in the conversation.
If no tools are needed, simply provide a direct answer or explanation.
"""

# Default personality component that can be customized
DEFAULT_PERSONALITY = "You are an intelligent assistant. You can think step-by-step. When users need specific information, you should use available tools to obtain it."

class DeepSeekModel(BaseModel):
    """
    Implementation of BaseModel for DeepSeek models with native tool calling.
    
    Uses the OpenAI-compatible API provided by DeepSeek to leverage native tool calling capabilities.
    """
    
    def __init__(self):
        """
        Initialize the DeepSeek model.
        """
        self.client = OpenAI(
            base_url=config.get('deepseek.base_url', 'https://api.deepseek.com'),
            api_key=config.get('deepseek.api_key')
        )
        self.model = config.get('deepseek.model', 'deepseek-chat')
        
        # Get system prompt from config, or use default personality
        custom_system_prompt = config.get('agent.custom_system_prompt', DEFAULT_PERSONALITY)
        
        # Combine the custom prompt with the required tool calling instructions
        complete_system_prompt = f"{custom_system_prompt}\n\n{TOOL_CALLING_INSTRUCTIONS}"
        
        # Create conversation history with the complete system prompt
        self.history = ConversationHistory(complete_system_prompt)
        
        self.history_adapter = DeepSeekHistoryAdapter()

    async def execute(self, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute the model with the current conversation history.
        
        Args:
            tools: List of tools available to the model
            
        Returns:
            Response with content and optional tool calls
        """
        try:
            # Debug output for raw history
            raw_history = self.history.format_debug_output()
            
            # Format history for DeepSeek using the adapter
            formatted_messages = self.history_adapter.format_for_model(
                self.history.get_messages(), tools
            )
            
            # Debug output for formatted history
            adapter_debug = self.history_adapter.format_debug_output(
                formatted_messages, tools, "DEEPSEEK INPUT"
            )

            # Call DeepSeek API with tools
            logger.debug(f"Calling DeepSeek model: {self.model}")
            response = await self._create_chat_completion(
                model=self.model,
                messages=formatted_messages,
                tools=tools if tools else None  # Only pass tools if provided
            )
            
            if not response or not response.choices:
                logger.error("Failed to get response from DeepSeek model")
                return create_error_response(LLMError("Failed to get response from model"))
                
            # Extract response data
            content = response.choices[0].message.content or ""
            logger.debug(f"Received response from DeepSeek: {content[:100]}...")
            
            # Extract reasoning content if available
            reasoning_content = None
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
                logger.debug(f"Reasoning content from DeepSeek: {reasoning_content}")
            
            # Extract tool calls directly from the response
            tool_calls = []
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                tool_calls = response.choices[0].message.tool_calls
                logger.debug(f"Tool calls found in response: {len(tool_calls)}")
                
                # Convert tool calls to the expected internal format
                formatted_tool_calls = []
                for tc in tool_calls:
                    formatted_tool_call = {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    formatted_tool_calls.append(formatted_tool_call)
                
                tool_calls = formatted_tool_calls
            
            # Return the processed response
            return {
                "choices": [{
                    "message": {
                        "content": content,
                        "tool_calls": tool_calls if tool_calls else None,
                        "reasoning_content": reasoning_content
                    }
                }]
            }
                
        except Exception as e:
            error = handle_error(e)
            logger.error(f"Error in model execution: {error}")
            return create_error_response(error)

    async def _create_chat_completion(self, **kwargs) -> Any:
        """
        Handle API call to DeepSeek.
        
        Args:
            **kwargs: Arguments to pass to the API
            
        Returns:
            The API response or None if failed
        """
        try:
            result = self.client.chat.completions.create(**kwargs)
            return await result if hasattr(result, "__await__") else result
        except Exception as e:
            error = handle_error(e, {"kwargs": kwargs})
            logger.error(f"API call error: {error}")
            return None

    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            message: The user message content
        """
        self.history.add_user_message(message)
        
    def add_assistant_message(self, message: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            message: The assistant message content
            tool_calls: Optional list of tool calls made by the assistant
        """
        self.history.add_assistant_message(message, tool_calls)
        
    def add_tool_result(self, tool_name: str, result: str, tool_call_id: Optional[str] = None) -> None:
        """
        Add a tool result to the conversation history.
        
        Args:
            tool_name: Name of the tool that was called
            result: Result returned by the tool
            tool_call_id: Optional ID of the tool call this is responding to
        """
        self.history.add_tool_result(tool_name, result, tool_call_id)