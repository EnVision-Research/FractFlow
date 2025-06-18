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
    
    def __init__(
        self,
        # Provider配置
        provider: str = 'deepseek',
        
        # DeepSeek配置
        deepseek_api_key: Optional[str] = None,
        deepseek_base_url: str = 'https://api.deepseek.com',
        deepseek_model: str = 'deepseek-chat',
        deepseek_max_tokens: int = 4096,
        deepseek_temperature: float = 1.0,
        
        # OpenAI配置
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        openai_model: str = 'gpt-4',
        openai_tool_calling_model: str = 'gpt-3.5-turbo',
        openai_max_tokens: int = 4096,
        openai_temperature: float = 1.0,
        
        # Qwen配置
        qwen_api_key: Optional[str] = None,
        qwen_base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        qwen_model: str = 'qwen-plus',
        qwen_max_tokens: int = 4096,
        qwen_temperature: float = 1.0,

        # SiliconFlow配置
        siliconflow_api_key: Optional[str] = None,
        siliconflow_base_url: str = 'https://api.siliconflow.cn/v1/chat/completions',
        siliconflow_model: str = 'siliconflow-chat',
        siliconflow_max_tokens: int = 4096,
        siliconflow_temperature: float = 1.0,
        
        # Agent行为配置
        max_iterations: int = 10,
        custom_system_prompt: str = '',
        call_path: str = '',
        
        # 工具调用配置
        tool_calling_max_retries: int = 5,
        tool_calling_base_url: str = 'https://api.deepseek.com',
        tool_calling_model: str = 'deepseek-chat',
        tool_calling_version: str = 'stable',
        tool_calling_temperature: float = 0,
    ):
        """
        Initialize the config manager with configuration parameters.
        
        Args:
            provider: 模型提供商，可选: 'deepseek', 'openai', 'qwen'
            deepseek_api_key: DeepSeek API密钥，从环境变量DEEPSEEK_API_KEY自动读取
            deepseek_base_url: DeepSeek API基础URL
            deepseek_model: DeepSeek模型名称，推荐: 'deepseek-chat'
            deepseek_max_tokens: DeepSeek最大token数
            deepseek_temperature: DeepSeek温度参数，控制输出随机性
            openai_api_key: OpenAI API密钥，从环境变量COMPLETION_API_KEY自动读取
            openai_base_url: OpenAI API基础URL
            openai_model: OpenAI模型名称
            openai_tool_calling_model: OpenAI工具调用专用模型
            openai_max_tokens: OpenAI最大token数
            openai_temperature: OpenAI温度参数
            qwen_api_key: Qwen API密钥，从环境变量QWEN_API_KEY自动读取
            qwen_base_url: Qwen API基础URL
            qwen_model: Qwen模型名称
            qwen_max_tokens: Qwen最大token数
            qwen_temperature: Qwen温度参数
            max_iterations: Agent最大迭代次数，影响复杂任务处理深度
            custom_system_prompt: 自定义系统提示，用于调整Agent行为风格
            call_path: 调用路径，用于日志记录层次结构
            tool_calling_max_retries: 工具调用最大重试次数
            tool_calling_base_url: 工具调用API基础URL
            tool_calling_model: 工具调用使用的模型
            tool_calling_version: 工具调用版本，'stable'更稳定，'turbo'更快
            tool_calling_temperature: 工具调用温度参数
        """
        # 自动从环境变量读取API密钥
        if deepseek_api_key is None:
            deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        if openai_api_key is None:
            openai_api_key = os.getenv('COMPLETION_API_KEY')
        if qwen_api_key is None:
            qwen_api_key = os.getenv('QWEN_API_KEY')
        if siliconflow_api_key is None:
            siliconflow_api_key = os.getenv('SILICONFLOW_API_KEY')
        
        # 构建内部配置字典结构
        self._config = {
            'openai': {
                'api_key': openai_api_key,
                'base_url': openai_base_url,
                'model': openai_model,
                'tool_calling_model': openai_tool_calling_model,
                'max_tokens': openai_max_tokens,
                'temperature': openai_temperature,
            },
            'deepseek': {
                'api_key': deepseek_api_key,
                'base_url': deepseek_base_url,
                'model': deepseek_model,
                'max_tokens': deepseek_max_tokens,
                'temperature': deepseek_temperature,
            },
            'qwen': {
                'api_key': qwen_api_key,
                'base_url': qwen_base_url,
                'model': qwen_model,
                'max_tokens': qwen_max_tokens,
                'temperature': qwen_temperature,
            },
            'siliconflow': {
                'api_key': siliconflow_api_key,
                'base_url': siliconflow_base_url,
                'model': siliconflow_model,
                'max_tokens': siliconflow_max_tokens,
                'temperature': siliconflow_temperature,
            },
            'agent': {
                'max_iterations': max_iterations,
                'custom_system_prompt': custom_system_prompt,
                'provider': provider,
                'call_path': call_path,
            },
            'tool_calling': {
                'max_retries': tool_calling_max_retries,
                'base_url': tool_calling_base_url,
                'model': tool_calling_model,
                'version': tool_calling_version,
                'temperature': tool_calling_temperature,
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
            
        # Check if the key exists in the default configuration by creating a temporary default instance
        default_config = ConfigManager()._config
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

    def push_to_call_path(self, module_name: str) -> None:
        """
        Push a module name to the call path.
        
        Args:
            module_name: The module name to add to the call path
        """
        current_path = self.get('agent.call_path', '')
        if current_path:
            new_path = f"{current_path}->{module_name}"
        else:
            new_path = module_name
        self.set('agent.call_path', new_path)
    
    def get_call_path(self) -> str:
        """
        Get the current call path.
        
        Returns:
            The current call path as a string
        """
        return self.get('agent.call_path', '') 