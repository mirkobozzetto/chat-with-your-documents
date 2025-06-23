# src/__init__.py
"""
Modular RAG System Components

This package contains the separated components of the RAG system:
- document_management: Module containing document processing and selection logic
- VectorStoreManager: Manages vector database operations
- QAManager: Manages question answering and retrieval
- RAGOrchestrator: Main RAG orchestrator that coordinates all components
- AuthManager: Handles authentication and user management
"""

from .vector_stores import VectorStoreManager
from .qa_system import QAManager
from .rag_system.rag_orchestrator import RAGOrchestrator
from .auth.auth_manager import AuthManager

__all__ = [
    'VectorStoreManager',
    'QAManager',
    'RAGOrchestrator',
    'AuthManager'
]

__version__ = '1.0.0'
