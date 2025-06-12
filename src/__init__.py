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

from .document_processor import DocumentProcessor
from .vector_store_manager import VectorStoreManager
from .document_selector import DocumentSelector
from .qa_manager import QAManager
from .rag_orchestrator import OptimizedRAGSystem

__all__ = [
    'DocumentProcessor',
    'VectorStoreManager',
    'DocumentSelector',
    'QAManager',
    'OptimizedRAGSystem'
]

__version__ = '1.0.0'
