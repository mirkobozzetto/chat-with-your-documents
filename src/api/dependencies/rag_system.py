# src/api/dependencies/rag_system.py

from typing import Dict, Any, Optional
from fastapi import Depends

from src.rag_system import RAGOrchestrator
from src.api.models.auth_models import UserInfo
from .authentication import get_optional_current_user
import config

# Store user-specific RAG systems
_user_rag_systems: Dict[str, RAGOrchestrator] = {}

def get_rag_configuration() -> Dict[str, Any]:
    """Get RAG system configuration from environment"""
    return {
        "OPENAI_API_KEY": config.OPENAI_API_KEY,
        "EMBEDDING_MODEL": config.EMBEDDING_MODEL,
        "CHAT_MODEL": config.CHAT_MODEL,
        "CHUNK_SIZE": config.CHUNK_SIZE,
        "CHUNK_OVERLAP": config.CHUNK_OVERLAP,
        "CHUNK_STRATEGY": config.CHUNK_STRATEGY,
        "CHAT_TEMPERATURE": config.CHAT_TEMPERATURE,
        "RETRIEVAL_K": config.RETRIEVAL_K,
        "RETRIEVAL_FETCH_K": config.RETRIEVAL_FETCH_K,
        "RETRIEVAL_LAMBDA_MULT": config.RETRIEVAL_LAMBDA_MULT,
        "VECTOR_STORE_TYPE": config.VECTOR_STORE_TYPE,
    }

def get_user_rag_system(
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
) -> RAGOrchestrator:
    """
    Get user-specific RAG system instance.
    Each user gets their own isolated RAG system to prevent data contamination.
    """
    user_id = current_user.username if current_user else "anonymous"

    if user_id not in _user_rag_systems:
        rag_config = get_rag_configuration()
        _user_rag_systems[user_id] = RAGOrchestrator(rag_config)

    return _user_rag_systems[user_id]

def get_shared_rag_system() -> RAGOrchestrator:
    """
    Get shared RAG system instance (for admin/system operations).
    Use sparingly - prefer get_user_rag_system for user operations.
    """
    rag_config = get_rag_configuration()
    return RAGOrchestrator(rag_config)
