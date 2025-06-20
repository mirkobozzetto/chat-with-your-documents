# src/api/routers/documents.py

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from typing import List, Optional
import os
import tempfile
import time
from pathlib import Path

from src.api.models.document_models import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentStatsResponse,
    DocumentSelectionRequest,
    DocumentSelectionResponse,
    KnowledgeBaseStatsResponse
)
from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        start_time = time.time()

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            rag_system.process_document(tmp_file_path)

            processing_time = time.time() - start_time

            available_docs = rag_system.get_available_documents()
            chunk_count = None
            if file.filename in available_docs:
                doc_info = rag_system.get_document_info(file.filename)
                chunk_count = doc_info.get("chunk_count") if doc_info else None

            return DocumentUploadResponse(
                filename=file.filename,
                status="success",
                message=f"Document '{file.filename}' processed successfully",
                processing_time=processing_time,
                chunk_count=chunk_count
            )

        finally:
            os.unlink(tmp_file_path)

    except Exception as e:
        return DocumentUploadResponse(
            filename=file.filename,
            status="error",
            message=f"Error processing document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()

        documents = []
        for doc_name in available_docs:
            doc_info = rag_system.get_document_info(doc_name)
            if doc_info:
                document = DocumentInfo(
                    filename=doc_name,
                    document_type=doc_info.get("document_type", "unknown"),
                    chunk_count=doc_info.get("chunk_count", 0),
                    metadata=doc_info.get("metadata", {})
                )
                documents.append(document)

        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_name}/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    document_name: str,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_name}' not found"
            )

        doc_info = rag_system.get_document_info(document_name)
        if not doc_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document info for '{document_name}' not found"
            )

        return DocumentStatsResponse(
            filename=document_name,
            chunk_count=doc_info.get("chunk_count", 0),
            total_characters=doc_info.get("total_characters", 0),
            average_chunk_size=doc_info.get("average_chunk_size", 0.0),
            metadata_summary=doc_info.get("metadata", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document stats: {str(e)}"
        )


@router.post("/select", response_model=DocumentSelectionResponse)
async def select_document(
    request: DocumentSelectionRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if request.filename not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{request.filename}' not found"
            )

        rag_system.set_selected_document(request.filename)

        return DocumentSelectionResponse(
            selected_document=rag_system.selected_document,
            available_documents=available_docs
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error selecting document: {str(e)}"
        )


@router.delete("/select")
async def clear_document_selection(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        rag_system.clear_selected_document()
        available_docs = rag_system.get_available_documents()

        return DocumentSelectionResponse(
            selected_document=None,
            available_documents=available_docs
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing document selection: {str(e)}"
        )


@router.delete("/{document_name}")
async def delete_document(
    document_name: str,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        available_docs = rag_system.get_available_documents()
        if document_name not in available_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_name}' not found"
            )

        success = rag_system.delete_document(document_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document '{document_name}'"
            )

        return {"message": f"Document '{document_name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/stats/knowledge-base", response_model=KnowledgeBaseStatsResponse)
async def get_knowledge_base_stats(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        stats = rag_system.get_knowledge_base_stats()

        return KnowledgeBaseStatsResponse(
            total_documents=stats.get("total_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
            vector_store_type=stats.get("vector_store_type", "unknown"),
            embedding_model=stats.get("embedding_model", "unknown"),
            chat_model=stats.get("chat_model", "unknown"),
            chunk_strategy=stats.get("chunk_strategy", "unknown"),
            retrieval_config=stats.get("retrieval_config", {}),
            selected_document=rag_system.selected_document
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving knowledge base stats: {str(e)}"
        )
