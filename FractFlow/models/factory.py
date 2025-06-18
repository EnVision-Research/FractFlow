"""
Model factory.

Factory for creating model implementations based on provider type.
"""

from typing import Optional
from .base_model import BaseModel
from ..infra.config import ConfigManager
from ..infra.logging_utils import get_logger

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
    
    # Push models to call path
    config.push_to_call_path("models")
    
    # Initialize logger
    logger = get_logger(config.get_call_path())
        
    # Use provider from args, or from config, or default to openai
    provider = provider or config.get('agent.provider', 'deepseek')
    
    logger.debug(f"Creating model", {"provider": provider})
    
    if provider == 'deepseek':
        from .deepseek_model import DeepSeekModel
        model = DeepSeekModel(config=config)
        logger.info(f"Created DeepSeek model")
        return model
    elif provider == 'qwen':
        from .qwen_model import QwenModel
        model = QwenModel(config=config)
        logger.info(f"Created Qwen model")
        return model
    elif provider == 'siliconflow':
        from .siliconflow_model import SiliconFlowModel
        model = SiliconFlowModel(config=config)
        logger.info(f"Created SiliconFlow model")
        return model
    elif provider == 'openai':
        # Note: This part would be properly implemented when OpenAIModel is created
        # For now, raising an error to indicate it's not implemented yet
        logger.error(f"OpenAI provider not implemented")
        raise NotImplementedError("OpenAI provider support is not yet implemented")
    else:
        logger.error(f"Unsupported provider", {"provider": provider})
        raise ValueError(f"Unsupported AI provider: {provider}") 