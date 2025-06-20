# src/api/routers/system.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional

from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator
from src.chat_history.session_manager import ConversationHistoryManager

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def get_system_status(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        return {
            "status": "operational",
            "version": "1.0.0",
            "has_documents": len(rag_system.get_available_documents()) > 0,
            "vector_store_ready": rag_system.vector_store_manager.has_documents(),
            "qa_ready": rag_system.qa_manager.is_ready(),
            "auth_enabled": rag_system.config.get("AUTH_ENABLED", False),
            "current_user": current_user.username if current_user else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system status: {str(e)}"
        )


@router.get("/info")
async def get_system_info(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        stats = rag_system.get_knowledge_base_stats()

        return {
            "system": {
                "name": "RAG Assistant API",
                "version": "1.0.0",
                "description": "Retrieval-Augmented Generation system"
            },
            "configuration": {
                "vector_store_type": stats.get("vector_store_type", "unknown"),
                "embedding_model": stats.get("embedding_model", "unknown"),
                "chat_model": stats.get("chat_model", "unknown"),
                "chunk_strategy": stats.get("chunk_strategy", "unknown"),
                "retrieval_config": stats.get("retrieval_config", {})
            },
            "statistics": {
                "total_documents": stats.get("total_documents", 0),
                "total_chunks": stats.get("total_chunks", 0),
                "selected_document": rag_system.selected_document
            },
            "capabilities": {
                "supported_formats": ["PDF", "DOCX", "TXT", "MD"],
                "vector_stores": ["Chroma", "Qdrant"],
                "features": [
                    "Document upload and processing",
                    "Question answering with RAG",
                    "Agent configuration",
                    "Conversation management",
                    "Debug and tuning tools",
                    "Authentication (optional)"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system info: {str(e)}"
        )


@router.get("/statistics")
async def get_system_statistics(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        history_manager = ConversationHistoryManager()
        conversation_stats = history_manager.get_statistics()
        kb_stats = rag_system.get_knowledge_base_stats()

        agent_manager = rag_system.qa_manager.get_agent_manager()
        available_docs = rag_system.get_available_documents()

        configured_agents = 0
        active_agents = 0
        for doc_name in available_docs:
            agent_config = agent_manager.get_agent_for_document(doc_name)
            if agent_config:
                configured_agents += 1
                if agent_config.is_active:
                    active_agents += 1

        return {
            "knowledge_base": {
                "total_documents": kb_stats.get("total_documents", 0),
                "total_chunks": kb_stats.get("total_chunks", 0),
                "vector_store_type": kb_stats.get("vector_store_type", "unknown")
            },
            "conversations": conversation_stats,
            "agents": {
                "total_configured": configured_agents,
                "active": active_agents,
                "available_types": len([
                    "conversational", "technical", "commercial",
                    "analytical", "educational", "creative"
                ])
            },
            "system": {
                "embedding_model": kb_stats.get("embedding_model", "unknown"),
                "chat_model": kb_stats.get("chat_model", "unknown"),
                "chunk_strategy": kb_stats.get("chunk_strategy", "unknown")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system statistics: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_system(
    days_threshold: int = 30,
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        history_manager = ConversationHistoryManager()
        deleted_conversations = history_manager.cleanup_old_conversations(days_threshold)

        return {
            "message": f"Cleanup completed",
            "deleted_conversations": deleted_conversations,
            "days_threshold": days_threshold
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        )
