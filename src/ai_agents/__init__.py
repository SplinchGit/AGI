"""
AI Agent Implementations
- Claude Builder: Code generation, debugging, optimization, architecture
- Qwen Brain: Strategic planning, analysis, decision-making, pattern recognition  
- Shared: Common utilities, communication, memory, metrics, workflow
"""

from . import claude_builder
from . import qwen_brain
from . import shared

__all__ = ['claude_builder', 'qwen_brain', 'shared']