# src/vector_stores/__init__.py
"""
Vector Store Management

Provides abstraction layer for different vector databases:
- ChromaVectorStoreManager: Local ChromaDB storage
- QdrantVectorStoreManager: Qdrant cloud storage
- VectorStoreFactory: Factory pattern for store selection
"""

from .vector_store_factory import VectorStoreFactory
from .base_vector_store import BaseVectorStoreManager
from .chroma_vector_store import ChromaVectorStoreManager
from .qdrant_vector_store import QdrantVectorStoreManager

__all__ = [
    'VectorStoreFactory',
    'BaseVectorStoreManager',
    'ChromaVectorStoreManager',
    'QdrantVectorStoreManager'
]
