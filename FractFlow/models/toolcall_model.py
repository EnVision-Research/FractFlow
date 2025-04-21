import json
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple

from openai import OpenAI

from ..infra.config import ConfigManager
from ..infra.error_handling import handle_error

logger = logging.getLogger(__name__)

class ToolCallHelper:
    """
    Tool calling helper for generating tool calls from instructions.
    
    Uses OpenAI-compatible APIs to generate tool calls in a standardized format.
    Can be configured to work with different model providers through configuration.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the tool calling helper with configuration.
        
        Args:
            config: Configuration manager instance to use
        """
        self.config = config or ConfigManager()
        self.client = None
        
        # Load configuration with defaults
        self.max_retries = self.config.get('tool_calling.max_retries', 5)
        self.base_url = self.config.get('tool_calling.base_url', 'https://api.deepseek.com')
        self.api_key = self.config.get('tool_calling.api_key', self.config.get('deepseek.api_key'))
        self.model = self.config.get('tool_calling.model', 'deepseek-chat')
        
    async def initialize_client(self) -> OpenAI:
        """
        Initialize the OpenAI-compatible client.
        
        Returns:
            Configured OpenAI client
        """
        if self.client is None:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        return self.client
        
    def create_system_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        Create a system prompt for JSON tool calling.
        
        Args:
            tools: List of available tools
            
        Returns:
            System prompt for the tool calling model
        """
        # List all available tools with names and descriptions
        tool_details = []
        for tool in tools:
            tool_name = tool['function']['name']
            description = tool['function'].get('description', 'No description available')
            
            # List all parameters for this tool
            params = tool['function'].get('parameters', {}).get('properties', {})
            param_list = ", ".join(params.keys()) if params else "No parameters"
            
            tool_details.append(f"- {tool_name}: {description}\n  Parameters: {param_list}")
        
        tools_text = "\n".join(tool_details)
        
        return f"""You are a tool calling expert. Your task is to generate correct JSON format tool calls based ONLY on the tools that are available.

AVAILABLE TOOLS (ONLY USE THESE - DO NOT INVENT NEW ONES):
{tools_text}

IMPORTANT RULES:
1. ONLY use tool names from the list above - never invent new tool names
2. ONLY use parameter names that are listed for each tool - never invent new parameters
3. If a requested tool doesn't exactly match any available tool, use the closest matching one
4. YOU CAN USE MULTIPLE TOOLS OR THE SAME TOOL MULTIPLE TIMES if the request requires it
5. If only one tool is needed, still use the proper array format with a single element

You must output strictly in the following JSON format:
{{
    "tool_calls": [
        {{
            "function": {{
                "name": "tool_name",
                "arguments": "{{\\\"parameter_name\\\": \\\"parameter_value\\\"}}",
            }}
        }},
        {{
            "function": {{
                "name": "another_tool_name",
                "arguments": "{{\\\"parameter_name\\\": \\\"parameter_value\\\"}}",
            }}
        }}
    ]
}}

The number of tool calls in the array should match exactly what's needed - don't add unnecessary calls.
For simple requests needing only one tool call, return an array with just one element.
Output JSON only, no other text. The arguments must be a valid JSON string (with escaped quotes)."""
    
    async def _create_chat_completion(self, **kwargs) -> Any:
        """
        Handle API call to the model provider.
        
        Args:
            **kwargs: Arguments to pass to the chat completions API
            
        Returns:
            The API response or None if failed
        """
        try:
            # Make sure client is initialized
            if not self.client:
                await self.initialize_client()
                
            # Add model if not provided
            if 'model' not in kwargs:
                kwargs['model'] = self.model
                
            # Call the API
            result = self.client.chat.completions.create(**kwargs)
            return await result if hasattr(result, "__await__") else result
        except Exception as e:
            error = handle_error(e, {"kwargs": kwargs})
            logger.error(f"API call error: {error}")
            return None
    
    async def _parse_model_response(self, response: Any) -> Optional[List[Dict[str, Any]]]:
        """
        Parse the response from the model into a list of tool calls.
        
        Args:
            response: Raw response from the model
            
        Returns:
            List of tool calls or None if failed
        """
        if not response or not response.choices:
            return None
            
        content = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            model_response = json.loads(content)
            
            # Process multiple tool calls
            if "tool_calls" in model_response and isinstance(model_response["tool_calls"], list):
                # Handle standard multiple tool calls format
                tool_calls = []
                for i, call_data in enumerate(model_response["tool_calls"]):
                    if "function" not in call_data:
                        logger.error(f"Tool call {i+1} has no function object")
                        continue
                        
                    # Add ID and type fields to each call
                    call_id = self.generate_call_id()
                    tool_call = {
                        "id": call_id,
                        "type": "function",
                        "function": call_data.get("function", {})
                    }
                    tool_calls.append(tool_call)
                
                return tool_calls
                
            # Handle single tool call format (for backward compatibility)
            elif "function" in model_response:
                # Convert single tool call to list format
                call_id = self.generate_call_id()
                tool_call = {
                    "id": call_id,
                    "type": "function",
                    "function": model_response.get("function", {})
                }
                
                return [tool_call]
            else:
                logger.error("Response does not contain tool_calls array or function object")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}\nContent: {content}...")
            return None
    
    async def call_tool(self, instruction: str, tools: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute a tool call using retry mechanism.
        Can generate multiple tool calls from a single instruction.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            Tuple containing:
            - List of valid tool calls in OpenAI format
            - Stats dictionary with success/failure information
        """
        available_tools = [tool['function']['name'] for tool in tools]
        stats = {
            "attempts": 0,
            "success": False,
            "valid_calls": 0,
            "invalid_calls": 0,
            "total_calls": 0
        }
        
        # Try multiple times to get valid tool calls
        for attempt in range(self.max_retries):
            try:
                stats["attempts"] = attempt + 1
                logger.debug(f"Tool call attempt {attempt+1}/{self.max_retries}")
                
                # Call the internal method to get tool calls
                tool_calls = await self._internal_call_tool(instruction, tools)
                
                # Skip if no response was received
                if not tool_calls:
                    logger.warning(f"No response from model on attempt {attempt+1}")
                    continue
                
                stats["total_calls"] = len(tool_calls)
                
                # Validate each tool call and keep valid ones
                valid_tool_calls = []
                for i, call in enumerate(tool_calls):
                    if self._validate_tool_call(call, available_tools):
                        valid_tool_calls.append(call)
                        stats["valid_calls"] += 1
                    else:
                        logger.warning(f"Invalid tool call {i+1} on attempt {attempt+1}: {call}")
                        stats["invalid_calls"] += 1
                
                # If we have at least one valid call, consider it a success
                if valid_tool_calls:
                    logger.debug(f"Generated {len(valid_tool_calls)} valid tool calls on attempt {attempt+1}")
                    stats["success"] = True
                    return valid_tool_calls, stats
                else:
                    logger.warning(f"No valid tool calls on attempt {attempt+1}")
                    continue
                
            except Exception as e:
                error = handle_error(e, {"instruction": instruction, "attempt": attempt+1})
                logger.error(f"Error on tool call attempt {attempt+1}: {error}")
                # Continue to the next attempt rather than failing immediately
        
        # If we exhausted all retries without success
        logger.error(f"Failed to generate valid tool calls after {self.max_retries} attempts")
        stats["success"] = False
        return [], stats
    
    async def _internal_call_tool(self, instruction: str, tools: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Internal method to call the model and get tool call responses.
        
        Args:
            instruction: The instruction to execute
            tools: List of available tools
            
        Returns:
            List of tool calls or None if failed
        """
        try:
            # Call the model with appropriate formatting
            response = await self._create_chat_completion(
                messages=[
                    {"role": "system", "content": self.create_system_prompt(tools)},
                    {"role": "user", "content": instruction}
                ],
                response_format={"type": "json_object"}
            )
            
            if not response:
                return None
            
            # Parse the response
            return await self._parse_model_response(response)
                
        except Exception as e:
            error = handle_error(e, {"instruction": instruction})
            logger.error(f"Internal tool calling error: {error}")
            return None
    
    def _validate_tool_call(self, tool_call: Dict[str, Any], available_tools: List[str]) -> bool:
        """
        Validate that a tool call has the correct format and references an available tool.
        
        Args:
            tool_call: The tool call to validate
            available_tools: List of available tool names
            
        Returns:
            True if the tool call is valid, False otherwise
        """
        # Check that the required fields are present
        if not isinstance(tool_call, dict):
            logger.error("Tool call is not a dictionary")
            return False
            
        if "type" not in tool_call or tool_call["type"] != "function":
            logger.error("Tool call is not a function call")
            return False
            
        if "function" not in tool_call or not isinstance(tool_call["function"], dict):
            logger.error("Tool call has no function object")
            return False
            
        function = tool_call["function"]
        if "name" not in function or "arguments" not in function:
            logger.error("Function object missing name or arguments")
            return False
            
        # Verify that the tool exists
        tool_name = function["name"]
        if tool_name not in available_tools:
            logger.error(f"Tool '{tool_name}' not in available tools: {available_tools}")
            return False
            
        # Verify that the arguments is a valid JSON string
        arguments = function["arguments"]
        if not isinstance(arguments, str):
            logger.error("Arguments must be a string")
            return False
            
        try:
            # Attempt to parse the arguments as JSON
            json.loads(arguments)
        except json.JSONDecodeError:
            logger.error(f"Arguments is not valid JSON: {arguments}...")
            return False
            
        # Everything looks good
        return True
            
    def generate_call_id(self) -> str:
        """
        Generate a unique ID for a tool call.
        
        Returns:
            Unique ID string
        """
        return f"call_{str(uuid.uuid4())[:8]}"
