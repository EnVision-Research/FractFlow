"""
Model factory.

Factory for creating model implementations based on provider type.
"""

from typing import Optional
from .base_model import BaseModel
from ..infra.config import ConfigManager

def create_model(provider: Optional[str] = None, config: Optional[ConfigManager] = None) -> BaseModel:
    """
    Factory function to create an appropriate model based on the provider.
    
    Args:
        provider: The AI provider to use (e.g., 'openai', 'deepseek', 'qwen')
        config: Configuration manager instance to use
        
    Returns:
        An instance of BaseModel
        
    Raises:
        ImportError: If the specified provider module cannot be loaded
        ValueError: If the specified provider is not supported
    """
    # 如果没有提供config，创建默认config
    if config is None:
        config = ConfigManager()
        
    # Use provider from args, or from config, or default to openai
    provider = provider or config.get('agent.provider', 'deepseek')
    
    if provider == 'deepseek':
        from .deepseek_model import DeepSeekModel
        return DeepSeekModel(config=config)
    elif provider == 'qwen':
        from .qwen_model import QwenModel
        return QwenModel(config=config)
    elif provider == 'openai':
        # Note: This part would be properly implemented when OpenAIModel is created
        # For now, raising an error to indicate it's not implemented yet
        raise NotImplementedError("OpenAI provider support is not yet implemented")
    else:
        raise ValueError(f"Unsupported AI provider: {provider}") 