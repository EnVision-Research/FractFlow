"""
Qwen history adapter.

Formats conversation history according to Qwen's API requirements.
"""

from typing import List, Dict, Any, Optional
from .base_adapter import HistoryAdapter

class QwenHistoryAdapter(HistoryAdapter):
    """
    History adapter for Qwen models.
    
    Formats conversation history according to Qwen's requirements.
    This adapter follows the same pattern as DeepSeek to ensure consistency.
    """
    # All implementations moved to base class
    pass 