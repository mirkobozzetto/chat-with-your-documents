# src/agents/__init__.py
"""
Agents System for RAG

Provides customizable AI agents with different behaviors:
- AgentManager: Main orchestrator for agent selection and prompt building
- AgentType: Available agent personalities and behaviors
- AgentConfigManager: Persistence and configuration management
- PromptTemplates: Specialized prompts for each agent type
"""

from .agent_manager import AgentManager
from .agent_types import AgentType, AgentBehavior, get_agent_behavior, get_available_agent_types
from .agent_config import AgentConfiguration, AgentConfigManager
from .prompt_templates import get_prompt_template, build_prompt

__all__ = [
    'AgentManager',
    'AgentType',
    'AgentBehavior',
    'AgentConfiguration',
    'AgentConfigManager',
    'get_agent_behavior',
    'get_available_agent_types',
    'get_prompt_template',
    'build_prompt'
]

__version__ = '1.0.0'
