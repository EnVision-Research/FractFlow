"""
OpenAI history adapter.

Formats conversation history according to OpenAI's API requirements.
"""

from typing import List, Dict, Any, Optional
from .base_adapter import HistoryAdapter

class OpenAIHistoryAdapter(HistoryAdapter):
    """
    History adapter for OpenAI models.
    
    Formats conversation history according to OpenAI's requirements.
    OpenAI models typically expect alternating user and assistant messages,
    with tools information embedded in the content rather than as separate roles.
    """
    # All implementations moved to base class
    pass 