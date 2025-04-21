"""
Qwen model implementation.

Provides implementation of the BaseModel interface for Qwen models.
"""

from typing import Dict, List, Any, Optional

from .orchestrator_model import OrchestratorModel
from ..infra.config import ConfigManager
from ..conversation.provider_adapters.qwen_adapter import QwenHistoryAdapter

class QwenModel(OrchestratorModel):
    """
    Implementation of OrchestratorModel for Qwen models.
    
    Handles user interaction, understands requirements, and generates
    high-quality tool calling instructions using Qwen's models.
    """
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize the Qwen model with Qwen-specific configuration.
        
        Args:
            config: Configuration manager instance to use
        """
        if config is None:
            config = ConfigManager()
            
        history_adapter = QwenHistoryAdapter()
        
        super().__init__(
            base_url=config.get('qwen.base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            api_key=config.get('qwen.api_key'),
            model_name=config.get('qwen.model', 'qwen-max'),
            provider_name='qwen',
            history_adapter=history_adapter,
            config=config
        )