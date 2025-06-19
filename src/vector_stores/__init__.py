# src/vector_stores/__init__.py
"""
Vector Store Management

VectorStoreManager: Simple ChromaDB vector store manager (legacy)
VectorStoreFactory: Factory pattern for creating vector stores
BaseVectorStoreManager: Abstract base for vector store implementations
ChromaVectorStoreManager: Local ChromaDB storage implementation
QdrantVectorStoreManager: Qdrant cloud storage implementation
"""

from .vector_store_manager import VectorStoreManager
from .vector_store_factory import VectorStoreFactory
from .base_vector_store import BaseVectorStoreManager
from .chroma_vector_store import ChromaVectorStoreManager
from .qdrant_vector_store import QdrantVectorStoreManager

__all__ = [
    'VectorStoreManager',
    'VectorStoreFactory',
    'BaseVectorStoreManager',
    'ChromaVectorStoreManager',
    'QdrantVectorStoreManager'
]
