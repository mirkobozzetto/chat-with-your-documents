"""
LangGraph Integration Module
Provides workflow orchestration using LangGraph
"""

from typing import Optional

__all__ = [
    "create_workflow",
    "WorkflowConfig"
]

def create_workflow(config: Optional[dict] = None):
    """
    Factory function to create LangGraph workflows
    Lazy loads to avoid import overhead
    """
    from .workflow import WorkflowOrchestrator
    return WorkflowOrchestrator(config or {})

class WorkflowConfig:
    """Configuration for LangGraph workflows"""
    def __init__(self):
        self.mode = "single_agent"
        self.enable_checkpointing = False
        self.enable_streaming = True
