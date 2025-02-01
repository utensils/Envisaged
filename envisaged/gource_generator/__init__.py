"""
Gource video generator package for creating Git repository visualizations.
"""

from .generator import GourceGenerator
from .config import GourceConfig
from .cli import main as cli

__all__ = ['GourceGenerator', 'GourceConfig', 'cli']
