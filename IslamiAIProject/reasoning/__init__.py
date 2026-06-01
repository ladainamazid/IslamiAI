"""
reasoning/__init__.py
─────────────────────────────────────────────────────────────────
Public interface dari reasoning package.

Penggunaan dari chatbot.py:
  from reasoning import ReasoningOrchestrator
  
Atau versi lengkap:
  from reasoning.orchestrator import ReasoningOrchestrator
  from reasoning.base_layer import LayerResult, LayerException
"""

from .orchestrator import ReasoningOrchestrator, ReasoningReport
from .base_layer import LayerResult, LayerException

__all__ = [
    "ReasoningOrchestrator",
    "ReasoningReport",
    "LayerResult",
    "LayerException",
]

__version__ = "2.0.0"
__author__ = "IslamiAIProject"
