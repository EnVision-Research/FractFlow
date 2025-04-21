"""
DeepSeek history adapter.

Formats conversation history according to DeepSeek's API requirements.
"""

from typing import List, Dict, Any, Optional
from .base_adapter import HistoryAdapter

class DeepSeekHistoryAdapter(HistoryAdapter):
    """
    History adapter for DeepSeek models.
    
    Formats conversation history according to DeepSeek's requirements.
    DeepSeek models typically expect alternating user and assistant messages,
    with tools information embedded in the content rather than as separate roles.
    """
    # All implementations moved to base class
    pass 