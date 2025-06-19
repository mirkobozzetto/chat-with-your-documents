# src/__init__.py
"""
Modular RAG System Components

This package contains the separated components of the RAG system:
- DocumentProcessor: Handles document loading and chunking
- VectorStoreManager: Manages ChromaDB operations
- DocumentSelector: Handles document filtering logic
- QAManager: Manages question answering and retrieval
- RAGOrchestrator: Coordinates all components
"""

from .document_management import DocumentProcessor, DocumentSelector
from .vector_store_manager import VectorStoreManager
from .qa_manager import QAManager
from .rag_orchestrator import OptimizedRAGSystem
from .auth.auth_manager import AuthManager

__all__ = [
    'DocumentProcessor',
    'VectorStoreManager',
    'DocumentSelector',
    'QAManager',
    'OptimizedRAGSystem',
    'AuthManager'
]

__version__ = '1.0.0'
