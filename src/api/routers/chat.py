# src/api/routers/chat.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import time

from src.api.models.chat_models import (
    QuestionRequest,
    QuestionResponse,
    ConversationSummaryResponse,
    ConversationResponse,
    CreateConversationRequest,
    SourceDocument
)
from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.middleware import get_quota_manager
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator
from src.chat_history.session_manager import SessionManager, ConversationHistoryManager

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        user_id = current_user.username if current_user else "anonymous"
        quota_manager = get_quota_manager()
        quota_manager.check_request_quota(user_id)

        estimated_tokens = len(request.question.split()) * 2
        quota_manager.check_token_quota(user_id, estimated_tokens)

        start_time = time.time()

        if request.document_filter:
            available_docs = rag_system.get_available_documents()
            if request.document_filter not in available_docs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{request.document_filter}' not found"
                )
            rag_system.set_selected_document(request.document_filter)

        result = rag_system.ask_question(request.question, request.chat_history)

        processing_time = time.time() - start_time

        source_documents = [
            SourceDocument(
                content=doc.page_content,
                metadata=doc.metadata,
                source_filename=doc.metadata.get("source_filename"),
                chunk_index=doc.metadata.get("chunk_index")
            )
            for doc in result.get("source_documents", [])
        ]

        response_tokens = len(result["result"].split()) * 1.3
        quota_manager.record_usage(user_id, int(estimated_tokens + response_tokens))

        return QuestionResponse(
            result=result["result"],
            source_documents=source_documents,
            metadata={
                "user": current_user.username if current_user else "anonymous",
                "timestamp": datetime.now().isoformat(),
                "document_filter": request.document_filter
            },
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationSummaryResponse])
async def get_conversations(
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        history_manager = ConversationHistoryManager()
        conversations = history_manager.list_recent_conversations()

        summaries = []
        for conv in conversations:
            summary = ConversationSummaryResponse(
                session_id=conv["session_id"],
                title=conv["title"],
                message_count=conv["message_count"],
                last_activity=conv["last_activity"],
                document_name=conv.get("document_name"),
                agent_type=conv.get("agent_type"),
                tags=[]
            )
            summaries.append(summary)

        return summaries

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversations: {str(e)}"
        )


@router.get("/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        session_manager = SessionManager()
        conversation = session_manager.load_session(session_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{session_id}' not found"
            )

        from src.api.models.chat_models import ChatMessageResponse
        messages = [
            ChatMessageResponse(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in conversation.messages
        ]

        return ConversationResponse(
            session_id=conversation.session_id,
            title=conversation.title,
            messages=messages,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            document_name=conversation.metadata.document_name,
            agent_type=conversation.metadata.agent_type
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        session_manager = SessionManager()
        conversation = session_manager.create_new_session(
            title=request.title,
            document_name=request.document_name,
            agent_type=request.agent_type
        )

        return ConversationResponse(
            session_id=conversation.session_id,
            title=conversation.title,
            messages=[],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            document_name=conversation.metadata.document_name,
            agent_type=conversation.metadata.agent_type
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating conversation: {str(e)}"
        )


@router.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        session_manager = SessionManager()
        success = session_manager.delete_session(session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{session_id}' not found"
            )

        return {"message": f"Conversation '{session_id}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting conversation: {str(e)}"
        )
