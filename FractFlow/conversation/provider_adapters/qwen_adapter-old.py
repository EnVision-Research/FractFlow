"""
QWEN history adapter.

Formats conversation history according to QWEN's API requirements.
"""

from typing import List, Dict, Any, Optional
import json
import uuid
from .base_adapter import HistoryAdapter

class QwenHistoryAdapter(HistoryAdapter):
    """
    History adapter for QWEN models.
    
    Formats conversation history according to QWEN's requirements.
    QWEN models typically follow an OpenAI-compatible format, with
    alternating user and assistant messages.
    """
    
    def format_for_model(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Format conversation history for QWEN models.
        
        Args:
            messages: The raw conversation history
            tools: Optional list of available tools
            
        Returns:
            Formatted conversation history for QWEN
        """
        formatted_messages = []
        tools_desc = None
        
        # Format tool descriptions if provided
        if tools:
            tools_desc = self._format_tools_description(tools)
        
        for i, message in enumerate(messages):
            role = message["role"]
            
            if role == "system":
                # System messages are directly supported
                formatted_messages.append({
                    "role": "system",
                    "content": message["content"]
                })
                
            elif role == "user":
                # For user messages, we might need to append tool descriptions
                content = message["content"]
                
                # Only append tools description to the last user message if needed
                if i == len(messages) - 1 and tools_desc and not any(self._contains_tool_desc(msg) for msg in formatted_messages):
                    content = f"{content}\n\nAvailable tools:\n{tools_desc}"
                    
                formatted_messages.append({
                    "role": "user",
                    "content": content
                })
                
            elif role == "assistant":
                # Assistant messages with tool calls
                if "tool_calls" in message and message["tool_calls"]:
                    # Convert internal tool call format to OpenAI compatible format
                    openai_tool_calls = []
                    for tc in message["tool_calls"]:
                        if isinstance(tc, dict):
                            # Generate a unique ID if not present
                            call_id = tc.get("id", f"call_{str(uuid.uuid4())[:8]}")
                            
                            # Extract name and arguments
                            name = tc.get("name", "")
                            
                            # If arguments is already a string, use it as is
                            # Otherwise, convert to JSON string
                            arguments = tc.get("arguments", {})
                            if not isinstance(arguments, str):
                                arguments = json.dumps(arguments)
                                
                            # Create OpenAI format tool call
                            openai_tool_calls.append({
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": arguments
                                }
                            })
                    
                    formatted_messages.append({
                        "role": "assistant",
                        "content": message["content"],
                        "tool_calls": openai_tool_calls
                    })
                else:
                    # Regular assistant messages
                    formatted_messages.append({
                        "role": "assistant", 
                        "content": message["content"]
                    })
                
            elif role == "tool":
                # Tool results need to be formatted as tool messages for QWEN
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": message.get("tool_call_id", ""),
                    "name": message.get("tool_name", "unknown_tool"),
                    "content": message["content"]
                })
        
        # Check if we have successive user messages and fix them
        self._ensure_alternating_messages(formatted_messages)
                
        return formatted_messages
    
    def _format_tools_description(self, tools: List[Dict[str, Any]]) -> str:
        """
        Format tool descriptions for inclusion in prompts.
        
        Args:
            tools: List of available tools
            
        Returns:
            Formatted string describing available tools
        """
        descriptions = []
        for tool in tools:
            name = tool.get("function", {}).get("name")
            description = tool.get("function", {}).get("description")
            params = tool.get("function", {}).get("parameters", {}).get("properties", {})
            
            if not name or not description:
                continue
                
            param_desc = []
            for param_name, param_info in params.items():
                param_type = param_info.get("type", "any")
                param_description = param_info.get("description", "")
                param_desc.append(f"  - {param_name} ({param_type}): {param_description}")
                
            param_text = "\n".join(param_desc) if param_desc else "  No parameters"
            descriptions.append(f"- {name}: {description}\n  Parameters:\n{param_text}")
            
        return "\n\n".join(descriptions)
    
    def _contains_tool_desc(self, message: Dict[str, Any]) -> bool:
        """
        Check if a message already contains tool descriptions.
        
        Args:
            message: The message to check
            
        Returns:
            True if the message contains tool descriptions, False otherwise
        """
        return (message.get("role") == "user" and 
                "Available tools:" in message.get("content", ""))
    
    def _ensure_alternating_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Ensure that user and assistant messages alternate properly.
        
        This is needed for QWEN models which require strict alternation.
        The function modifies the messages list in-place.
        
        Args:
            messages: The formatted messages to check and fix
        """
        # Skip if we only have system messages or empty list
        if len(messages) <= 1:
            return
            
        # Find the first non-system message
        start_idx = 0
        for i, msg in enumerate(messages):
            if msg["role"] != "system":
                start_idx = i
                break
                
        # Iterate through messages starting from first non-system
        i = start_idx
        while i < len(messages) - 1:
            current = messages[i]
            next_msg = messages[i+1]
            
            # If we have two consecutive messages of the same role (except system)
            if current["role"] == next_msg["role"] and current["role"] != "system":
                # Special handling for consecutive user messages
                if current["role"] == "user":
                    # Combine the content
                    combined_content = f"{current['content']}\n\n{next_msg['content']}"
                    messages[i]["content"] = combined_content
                    
                    # Remove the duplicate
                    messages.pop(i+1)
                    
                    # Don't increment i since we removed an element
                    continue
                    
                # Special handling for consecutive assistant messages
                elif current["role"] == "assistant":
                    # Combine the content
                    combined_content = f"{current['content']}\n\n{next_msg['content']}"
                    messages[i]["content"] = combined_content
                    
                    # Combine tool_calls if present
                    if "tool_calls" in current and "tool_calls" in next_msg:
                        messages[i]["tool_calls"] = current["tool_calls"] + next_msg["tool_calls"]
                    elif "tool_calls" in next_msg:
                        messages[i]["tool_calls"] = next_msg["tool_calls"]
                        
                    # Remove the duplicate
                    messages.pop(i+1)
                    
                    # Don't increment i since we removed an element
                    continue
            
            # Move to next message
            i += 1 