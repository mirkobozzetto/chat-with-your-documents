# src/__init__.py
"""
Modular RAG System Components

This package contains the separated components of the RAG system:
- document_management: Module containing document processing and selection logic
- VectorStoreManager: Manages vector database operations
- QAManager: Manages question answering and retrieval
- OptimizedRAGSystem: Main RAG orchestrator that coordinates all components
- AuthManager: Handles authentication and user management
"""

from .vector_store_manager import VectorStoreManager
from .qa_manager import QAManager
from .rag_system import OptimizedRAGSystem
from .auth.auth_manager import AuthManager

__all__ = [
    'VectorStoreManager',
    'QAManager',
    'OptimizedRAGSystem',
    'AuthManager'
]

__version__ = '1.0.0'
