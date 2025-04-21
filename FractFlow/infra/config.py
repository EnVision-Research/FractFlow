"""
Configuration management for the agent system.

Provides a unified interface for loading and accessing configuration
from various sources, including environment variables and config files.
"""

import os
import json
import copy
from typing import Any, Dict, Optional

class ConfigManager:
    """
    Manages configuration settings for the agent system.
    
    Provides a unified interface for accessing configuration values,
    allowing configuration to be set from various sources.
    """
    
    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the config manager with optional initial configuration.
        
        Args:
            initial_config: Optional initial configuration to use
        """
        # Initialize with default configuration
        self._config = self._get_default_config()
        
        # Apply initial config if provided
        if initial_config:
            self.set_config(initial_config)
            
        # Load environment variables after initial config
        self._load_from_env()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'openai': {
                'api_key': None,
                'base_url': None,
                'model': 'gpt-4',
                'tool_calling_model': 'gpt-3.5-turbo',
            },
            'deepseek': {
                'api_key': None,
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
            },
            'qwen': {
                'api_key': None,
                'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'model': 'qwen-plus',
            },
            'agent': {
                'max_iterations': 10,
                'custom_system_prompt': '',      # Field for customizable part of system prompt
                'provider': 'deepseek',          # Default provider is deepseek
            },
            'tool_calling': {
                'max_retries': 5,                # Maximum number of retries for tool calls
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration.
        
        Returns:
            A deep copy of the entire configuration dictionary
        """
        # Return a deep copy to prevent external modification of the internal state
        return copy.deepcopy(self._config)
    
    def create_copy(self) -> 'ConfigManager':
        """
        Create a new ConfigManager instance with the same configuration.
        
        Returns:
            A new ConfigManager instance with a copy of the current configuration
        """
        new_config = ConfigManager()
        new_config.set_config(self.get_config())
        return new_config
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set multiple configuration values at once.
        
        Args:
            config: Configuration dictionary to set
            
        Raises:
            KeyError: If any key does not exist in the default configuration structure
        """
        # Process each section in the config
        for section, values in config.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if value is not None:  # Skip None values
                        self.set(f"{section}.{key}", value)
            elif values is not None:  # Handle direct values like 'provider'
                self.set(section, values)
    
    def _load_from_env(self, env_vars: Optional[Dict[str, str]] = None) -> None:
        """
        Load API keys from environment variables. Other configuration values 
        will use defaults from _get_default_config.
        
        Args:
            env_vars: Optional dictionary of environment variables.
                     If not provided, will use os.environ.
        """
        # Use provided env_vars or os.environ
        env = env_vars or os.environ
        
        # Only load API keys from environment variables
        self.set('openai.api_key', env.get('COMPLETION_API_KEY'))
        self.set('deepseek.api_key', env.get('DEEPSEEK_API_KEY'))
        self.set('qwen.api_key', env.get('QWEN_API_KEY'))
        
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g. 'openai.api_key')
            default: Default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        parts = key.split('.')
        value = self._config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value (e.g. 'openai.api_key')
            value: The value to set
            
        Raises:
            KeyError: If the key does not exist in the default configuration structure
        """
        # Skip None values to prevent overriding defaults
        if value is None:
            return
            
        # Check if the key exists in the default configuration
        default_config = self._get_default_config()
        parts = key.split('.')
        check_config = default_config
        
        for part in parts:
            if isinstance(check_config, dict) and part in check_config:
                check_config = check_config[part]
            else:
                raise KeyError(f"Config key '{key}' does not exist in the default configuration structure")
        
        # If we got here, the key exists in the default config, so we can set it
        config = self._config
        
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
            
        config[parts[-1]] = value
    
    def load_from_file(self, file_path: str) -> None:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON configuration file
        """
        try:
            with open(file_path, 'r') as f:
                file_config = json.load(f)
                
            # Instead of deep merging manually, use the set_config method
            self.set_config(file_config)
        except Exception as e:
            print(f"Error loading configuration from {file_path}: {e}")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries.
        
        Args:
            target: The target dictionary to merge into
            source: The source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                if value is not None:  # Only set non-None values
                    target[key] = value 