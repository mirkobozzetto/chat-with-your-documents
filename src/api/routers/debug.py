# src/api/routers/debug.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import time

from src.api.models.debug_models import (
    RetrievalTestRequest,
    RetrievalTestResponse,
    RetrievalResult,
    SystemSettingsRequest,
    SystemSettingsResponse,
    VectorStoreAnalysisResponse
)
from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.post("/retrieval/test", response_model=RetrievalTestResponse)
async def test_retrieval(
    request: RetrievalTestRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        start_time = time.time()

        if request.document_filter:
            available_docs = rag_system.get_available_documents()
            if request.document_filter not in available_docs:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{request.document_filter}' not found"
                )
            rag_system.set_selected_document(request.document_filter)

        vector_store = rag_system.vector_store_manager.get_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No vector store available"
            )

        k = request.k or rag_system.config.get("RETRIEVAL_K", 6)

        results = vector_store.similarity_search_with_score(request.query, k=k)

        processing_time = time.time() - start_time

        retrieval_results = []
        for doc, score in results:
            retrieval_results.append(RetrievalResult(
                content=doc.page_content,
                score=float(score),
                metadata=doc.metadata,
                source_filename=doc.metadata.get("source_filename"),
                chunk_index=doc.metadata.get("chunk_index")
            ))

        parameters_used = {
            "k": k,
            "retrieval_fetch_k": rag_system.config.get("RETRIEVAL_FETCH_K", 25),
            "retrieval_lambda_mult": rag_system.config.get("RETRIEVAL_LAMBDA_MULT", 0.8),
            "document_filter": request.document_filter
        }

        return RetrievalTestResponse(
            query=request.query,
            results=retrieval_results,
            total_results=len(retrieval_results),
            processing_time=processing_time,
            parameters_used=parameters_used
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing retrieval: {str(e)}"
        )


@router.get("/settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        return SystemSettingsResponse(
            retrieval_k=rag_system.config.get("RETRIEVAL_K", 6),
            retrieval_fetch_k=rag_system.config.get("RETRIEVAL_FETCH_K", 25),
            retrieval_lambda_mult=rag_system.config.get("RETRIEVAL_LAMBDA_MULT", 0.8),
            chat_temperature=rag_system.config.get("CHAT_TEMPERATURE", 0.1),
            chunk_size=rag_system.config.get("CHUNK_SIZE", 1500),
            chunk_overlap=rag_system.config.get("CHUNK_OVERLAP", 300),
            chunk_strategy=rag_system.config.get("CHUNK_STRATEGY", "semantic")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system settings: {str(e)}"
        )


@router.patch("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    request: SystemSettingsRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        if request.retrieval_k is not None:
            if request.retrieval_k < 1 or request.retrieval_k > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="retrieval_k must be between 1 and 50"
                )
            rag_system.config["RETRIEVAL_K"] = request.retrieval_k

        if request.retrieval_fetch_k is not None:
            if request.retrieval_fetch_k < 1 or request.retrieval_fetch_k > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="retrieval_fetch_k must be between 1 and 100"
                )
            rag_system.config["RETRIEVAL_FETCH_K"] = request.retrieval_fetch_k

        if request.retrieval_lambda_mult is not None:
            if request.retrieval_lambda_mult < 0 or request.retrieval_lambda_mult > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="retrieval_lambda_mult must be between 0 and 1"
                )
            rag_system.config["RETRIEVAL_LAMBDA_MULT"] = request.retrieval_lambda_mult

        rag_system.qa_manager.create_qa_chain()

        return SystemSettingsResponse(
            retrieval_k=rag_system.config.get("RETRIEVAL_K", 6),
            retrieval_fetch_k=rag_system.config.get("RETRIEVAL_FETCH_K", 25),
            retrieval_lambda_mult=rag_system.config.get("RETRIEVAL_LAMBDA_MULT", 0.8),
            chat_temperature=rag_system.config.get("CHAT_TEMPERATURE", 0.1),
            chunk_size=rag_system.config.get("CHUNK_SIZE", 1500),
            chunk_overlap=rag_system.config.get("CHUNK_OVERLAP", 300),
            chunk_strategy=rag_system.config.get("CHUNK_STRATEGY", "semantic")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating system settings: {str(e)}"
        )


@router.get("/vector-store/analysis", response_model=VectorStoreAnalysisResponse)
async def analyze_vector_store(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        vector_store = rag_system.vector_store_manager.get_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No vector store available"
            )

        all_metadata = rag_system.vector_store_manager.get_all_metadata()
        total_chunks = len(all_metadata)

        unique_documents = set()
        total_content_length = 0
        metadata_fields = set()

        sample_chunks = []
        for i, metadata in enumerate(all_metadata[:5]):
            if "source_filename" in metadata:
                unique_documents.add(metadata["source_filename"])

            for key in metadata.keys():
                metadata_fields.add(key)

            try:
                docs = vector_store.similarity_search("sample", k=1)
                if docs:
                    total_content_length += len(docs[0].page_content)
                    if i < 3:
                        sample_chunks.append({
                            "content_preview": docs[0].page_content[:200] + "..." if len(docs[0].page_content) > 200 else docs[0].page_content,
                            "metadata": docs[0].metadata,
                            "content_length": len(docs[0].page_content)
                        })
            except:
                pass

        average_chunk_size = total_content_length / max(1, len(all_metadata[:100]))

        return VectorStoreAnalysisResponse(
            total_chunks=total_chunks,
            unique_documents=len(unique_documents),
            average_chunk_size=average_chunk_size,
            metadata_fields=list(metadata_fields),
            sample_chunks=sample_chunks
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing vector store: {str(e)}"
        )
