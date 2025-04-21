"""
Orchestrator model implementation.

Provides a base implementation for models that orchestrate tools and reasoning.
"""

import json
import logging
import re
import uuid
from typing import Dict, List, Any, Optional
from openai import OpenAI

from .base_model import BaseModel
from .toolcall_model import ToolCallHelper
from ..infra.config import ConfigManager
from ..infra.error_handling import LLMError, handle_error, create_error_response
from ..conversation.base_history import ConversationHistory

logger = logging.getLogger(__name__)

# Instructions for the main reasoner model on how to request a tool call
TOOL_REQUEST_INSTRUCTIONS = """When you determine that a tool is needed to answer the user's request or perform an action, you MUST issue a tool request instruction. 
Do NOT attempt to generate the final tool call JSON yourself.

To request a tool call, include the following tag anywhere in your response, containing the specific instruction for the tool:
<tool_request>Instruction text for the tool call expert here.</tool_request>

For example:
User: What's the weather in London?
Assistant: Okay, I can find that for you.
<tool_request>Get the current weather for London, UK.</tool_request>

If no tool is needed, simply provide a direct answer or explanation without the <tool_request> tag."""

# Default personality component that can be customized
DEFAULT_PERSONALITY = "You are an intelligent assistant. You carefully analyze user requests and determine if external tools are needed."


class OrchestratorModel(BaseModel):
    """
    Base implementation for models that orchestrate tool usage.
    
    Handles user interaction, understands requirements, and generates
    high-quality tool calling instructions using various LLM providers.
    """
    
    def __init__(self, base_url: str, api_key: str, model_name: str, provider_name: str, 
                 history_adapter: Any, config: Optional[ConfigManager] = None):
        """
        Initialize the orchestrator model with provider-specific settings.
        
        Args:
            base_url: The API base URL for the provider
            api_key: The API key for the provider
            model_name: The model name/identifier to use
            provider_name: Name of the provider for tool helper creation
            history_adapter: Provider-specific history adapter instance
            config: Configuration manager instance to use
        """
        if config is None:
            config = ConfigManager()
            
        self.config = config
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model_name
        
        # Get system prompt from config, or use default personality
        custom_system_prompt = config.get('agent.custom_system_prompt', DEFAULT_PERSONALITY)
        
        # Combine the custom prompt with the required tool calling instructions
        complete_system_prompt = f"{custom_system_prompt}\n\n{TOOL_REQUEST_INSTRUCTIONS}"
        
        # Create conversation history with the complete system prompt
        self.history = ConversationHistory(complete_system_prompt)
        
        self.history_adapter = history_adapter
        # Use the unified ToolCallHelper with provider name
        self.tool_helper = ToolCallHelper(config=config)

    async def execute(self, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Execute the model with the current conversation history.
        The model decides if a tool is needed and provides an instruction.
        If an instruction is found, it's passed to the tool_helper for robust generation.
        
        Args:
            tools: List of tools available to the model
            
        Returns:
            Response with content and optional tool calls
        """
        try:
            # Format history using the adapter
            # Pass tools=None here, as the main model only generates instructions, not calls
            formatted_messages = self.history_adapter.format_for_model(
                self.history.get_messages(), tools=None  
            )
            
            # Get model response
            logger.debug(f"Calling {self.__class__.__name__} model: {self.model}")
            response = await self._create_chat_completion(
                model=self.model,
                messages=formatted_messages
            )
            
            if not response or not response.choices:
                logger.error(f"Failed to get response from {self.__class__.__name__} model")
                return create_error_response(LLMError("Failed to get response from model"))
                
            content = response.choices[0].message.content
            logger.debug(f"Received response from reasoner: {content[:200]}...")
            
            # Extract reasoning content if available
            reasoning_content = None
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
                logger.debug(f"Reasoning content from reasoner: {reasoning_content}")

            # --- Multiple Tool Calling Logic ---
            tool_calls = []
            
            # Find all tool request tags
            matches = re.findall(r"<tool_request>(.*?)</tool_request>", content, re.DOTALL)
            
            if matches and tools:
                logger.debug(f"Found {len(matches)} tool request instructions")
                
                # Process each tool request
                for i, tool_instruction in enumerate(matches):
                    # Extract and clean the instruction text
                    tool_instruction = tool_instruction.strip()
                    logger.debug(f"Processing tool request {i+1}: {tool_instruction[:100]}...")
                    
                    # Pass the instruction to the robust tool calling helper
                    logger.debug(f"Invoking tool_helper for request {i+1}...")
                    validated_tool_calls, stats = await self.tool_helper.call_tool(tool_instruction, tools)
                    
                    if validated_tool_calls and len(validated_tool_calls) > 0:
                        # Add all valid tool calls to our list
                        tool_calls.extend(validated_tool_calls)
                        logger.info(f"Helper generated {stats['valid_calls']} tool calls for request {i+1}")
                    else:
                        logger.error(f"Tool helper failed to generate valid tool calls for request {i+1}")
                        
                if not tool_calls:
                    logger.warning("None of the tool requests produced valid tool calls")
            elif matches and not tools:
                logger.warning(f"Found {len(matches)} tool requests, but no tools were provided to execute")
            else:
                logger.debug("No <tool_request> tags found in the response")
            # --- End Multiple Tool Calling Logic ---

            # Return the response, including all validated tool calls
            return {
                "choices": [{
                    "message": {
                        "content": content, # Keep original content, including the tags for now
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
        Handle API call to model provider.
        
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