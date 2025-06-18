"""
SiliconFlow model implementation.

Provides implementation of the BaseModel interface for SiliconFlow models.
"""

import requests
import json
from typing import Optional, Any, Dict
from types import SimpleNamespace

from .orchestrator_model import OrchestratorModel
from ..infra.config import ConfigManager
from ..infra.logging_utils import get_logger
from ..conversation.provider_adapters.siliconflow_model import SiliconFlowHistoryAdapter

class SiliconFlowModel(OrchestratorModel):
    """
    Implementation of OrchestratorModel for SiliconFlow models.
    
    Handles user interaction, understands requirements, and generates
    high-quality tool calling instructions using SiliconFlow's models.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the SiliconFlow model with SiliconFlow-specific configuration.
        
        Args:
            config: Configuration manager instance to use
        """
        if config is None:
            config = ConfigManager()
            
        # Push model type to call path
        config.push_to_call_path("siliconflow")
        
        # Initialize logger
        self.logger = get_logger(config.get_call_path())
            
        history_adapter = SiliconFlowHistoryAdapter()
        
        self.logger.debug("Creating SiliconFlow model")
        
        super().__init__(
            base_url=config.get('siliconflow.base_url', 'https://api.siliconflow.cn/v1/chat/completions'),
            api_key=config.get('siliconflow.api_key'),
            model_name=config.get('siliconflow.model', 'siliconflow-chat'),
            provider_name='siliconflow',
            history_adapter=history_adapter,
            config=config
        )
        
        self.logger.debug("SiliconFlow model created", {
            "model": config.get('siliconflow.model', 'siliconflow-chat'),
            "base_url": config.get('siliconflow.base_url', 'https://api.siliconflow.cn/v1/chat/completions')
        })

    async def _create_chat_completion(self, **kwargs) -> Any:
        """
        Handle API call to SiliconFlow provider using requests.
        
        Args:
            **kwargs: Arguments to pass to the SiliconFlow API
            
        Returns:
            The API response formatted as OpenAI-compatible response or None if failed
        """
        try:
            # Add max_tokens and temperature to API call parameters if not already present
            if 'max_tokens' not in kwargs:
                kwargs['max_tokens'] = self.config.get(f'{self.provider_name}.max_tokens')
            
            if 'temperature' not in kwargs:
                kwargs['temperature'] = self.config.get(f'{self.provider_name}.temperature')
            
            # Prepare the SiliconFlow API payload
            payload = {
                "model": kwargs.get('model', self.model),
                "messages": kwargs.get('messages', []),
                "stream": kwargs.get('stream', False),
                "max_tokens": kwargs.get('max_tokens', 4096),
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.7),
                "top_k": kwargs.get('top_k', 50),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.5),
                "n": kwargs.get('n', 1),
                "response_format": kwargs.get('response_format', {"type": "text"}),
                "stop": kwargs.get('stop', None),
                "min_p": kwargs.get('min_p', 0.05),
                "enable_thinking": kwargs.get('enable_thinking', False),
                "thinking_budget": kwargs.get('thinking_budget', 4096)
            }
            
            # Add tools if provided
            if 'tools' in kwargs and kwargs['tools']:
                payload['tools'] = kwargs['tools']
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json"
            }
            
            # Log the request
            self.logger.debug(f"Making SiliconFlow API request", {
                "url": self.client.base_url,
                "model": payload['model'],
                "messages_count": len(payload['messages'])
            })
            
            # Make the HTTP request
            response = requests.post(
                url=self.client.base_url,
                json=payload,
                headers=headers,
                timeout=60  # 60 seconds timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            
            # Convert to OpenAI-compatible format
            openai_compatible_response = self._convert_to_openai_format(response_data)
            
            self.logger.debug("SiliconFlow API response received", {
                "status_code": response.status_code,
                "choices_count": len(openai_compatible_response.choices) if hasattr(openai_compatible_response, 'choices') else 0
            })
            
            return openai_compatible_response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SiliconFlow API request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse SiliconFlow API response: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in SiliconFlow API call: {str(e)}")
            return None

    def _convert_to_openai_format(self, siliconflow_response: Dict[str, Any]) -> Any:
        """
        Convert SiliconFlow API response to OpenAI-compatible format.
        
        Args:
            siliconflow_response: The raw response from SiliconFlow API
            
        Returns:
            OpenAI-compatible response object
        """
        try:
            # Create OpenAI-compatible response structure
            choices = []
            
            if 'choices' in siliconflow_response:
                for choice in siliconflow_response['choices']:
                    # Create message object
                    message = SimpleNamespace()
                    message.content = choice.get('message', {}).get('content', '')
                    message.role = choice.get('message', {}).get('role', 'assistant')
                    
                    # Add reasoning content if available (for thinking models)
                    if 'reasoning_content' in choice.get('message', {}):
                        message.reasoning_content = choice['message']['reasoning_content']
                    
                    # Add tool calls if available
                    if 'tool_calls' in choice.get('message', {}):
                        message.tool_calls = choice['message']['tool_calls']
                    
                    # Create choice object
                    choice_obj = SimpleNamespace()
                    choice_obj.message = message
                    choice_obj.finish_reason = choice.get('finish_reason', 'stop')
                    choice_obj.index = choice.get('index', 0)
                    
                    choices.append(choice_obj)
            
            # Create the main response object
            response = SimpleNamespace()
            response.choices = choices
            response.id = siliconflow_response.get('id', '')
            response.object = siliconflow_response.get('object', 'chat.completion')
            response.created = siliconflow_response.get('created', 0)
            response.model = siliconflow_response.get('model', '')
            
            # Add usage information if available
            if 'usage' in siliconflow_response:
                response.usage = SimpleNamespace()
                usage = siliconflow_response['usage']
                response.usage.prompt_tokens = usage.get('prompt_tokens', 0)
                response.usage.completion_tokens = usage.get('completion_tokens', 0)
                response.usage.total_tokens = usage.get('total_tokens', 0)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to convert SiliconFlow response to OpenAI format: {str(e)}")
            # Return a minimal response structure
            response = SimpleNamespace()
            response.choices = []
            return response