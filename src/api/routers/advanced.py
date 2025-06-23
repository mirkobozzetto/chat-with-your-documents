# src/api/routers/advanced.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from src.api.models.advanced_models import (
    AdvancedQuestionRequest,
    ConfigurationPreset, 
    ConfigurationResponse,
    ChunkingConfig,
    RetrievalConfig,
    WeightingConfig,
    FilterConfig
)
from src.api.models.chat_models import QuestionResponse, SourceDocument
from src.api.dependencies.rag_system import get_user_rag_system
from src.api.dependencies.authentication import get_optional_current_user
from src.api.models.auth_models import UserInfo
from src.rag_system import RAGOrchestrator

router = APIRouter(prefix="/api/advanced", tags=["advanced"])

@router.post("/ask", response_model=QuestionResponse)
async def ask_with_advanced_config(
    request: AdvancedQuestionRequest,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system),
    current_user: UserInfo = Depends(get_optional_current_user)
):
    try:
        if request.preset_name:
            preset_config = get_preset_configuration(request.preset_name)
            apply_preset_to_rag_system(rag_system, preset_config)
        
        if request.chunking_config:
            apply_chunking_config(rag_system, request.chunking_config)
            
        if request.retrieval_config:
            apply_retrieval_config(rag_system, request.retrieval_config)
            
        if request.weighting_config:
            apply_weighting_config(rag_system, request.weighting_config)
            
        if request.filter_config:
            apply_filter_config(rag_system, request.filter_config)

        result = rag_system.ask_question(request.question, request.chat_history)

        source_documents = [
            SourceDocument(
                content=doc.page_content,
                metadata=doc.metadata,
                source_filename=doc.metadata.get("source_filename"),
                chunk_index=doc.metadata.get("chunk_index")
            )
            for doc in result.get("source_documents", [])
        ]

        return QuestionResponse(
            result=result["result"],
            source_documents=source_documents,
            metadata={
                "advanced_config_applied": True,
                "preset_used": request.preset_name
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error with advanced configuration: {str(e)}"
        )

@router.get("/config", response_model=ConfigurationResponse)
async def get_current_config(
    rag_system: RAGOrchestrator = Depends(get_user_rag_system)
):
    current_config = extract_current_config(rag_system)
    available_presets = ["Default", "Academic", "Technical", "Creative"]
    
    return ConfigurationResponse(
        current_config=current_config,
        available_presets=available_presets
    )

@router.put("/config/chunking")
async def update_chunking_config(
    config: ChunkingConfig,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system)
):
    apply_chunking_config(rag_system, config)
    return {"message": "Chunking configuration updated"}

@router.put("/config/retrieval") 
async def update_retrieval_config(
    config: RetrievalConfig,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system)
):
    apply_retrieval_config(rag_system, config)
    return {"message": "Retrieval configuration updated"}

@router.put("/config/weighting")
async def update_weighting_config(
    config: WeightingConfig,
    rag_system: RAGOrchestrator = Depends(get_user_rag_system)
):
    apply_weighting_config(rag_system, config)
    return {"message": "Weighting configuration updated"}

@router.get("/presets/{preset_name}", response_model=ConfigurationPreset)
async def get_preset(preset_name: str):
    if preset_name not in ["Default", "Academic", "Technical", "Creative"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_name}' not found"
        )
    
    return get_preset_configuration(preset_name)

def apply_chunking_config(rag_system: RAGOrchestrator, config: ChunkingConfig):
    rag_system.chunk_size = config.chunk_size
    rag_system.chunk_overlap = config.chunk_overlap
    rag_system.chunk_strategy = config.chunk_strategy.value
    if config.semantic_threshold:
        rag_system.semantic_threshold = config.semantic_threshold

def apply_retrieval_config(rag_system: RAGOrchestrator, config: RetrievalConfig):
    rag_system.retrieval_k = config.retrieval_k
    rag_system.retrieval_fetch_k = config.fetch_k
    rag_system.retrieval_lambda_mult = config.lambda_mult

def apply_weighting_config(rag_system: RAGOrchestrator, config: WeightingConfig):
    if hasattr(rag_system, 'vector_store_manager'):
        weighting_system = getattr(rag_system.vector_store_manager, 'search_engine', None)
        if weighting_system:
            weighting_system.chapter_match_boost = config.chapter_match_boost
            weighting_system.section_match_boost = config.section_match_boost
            weighting_system.pdf_document_boost = config.pdf_document_boost
            weighting_system.early_position_boost = config.early_position_boost

def apply_filter_config(rag_system: RAGOrchestrator, config: FilterConfig):
    if config.document_filter:
        rag_system.set_document_filter(config.document_filter)
    if config.chapter_range != "All":
        rag_system.set_chapter_filter(config.chapter_range)
    rag_system.min_chunk_length = config.min_chunk_length

def apply_preset_to_rag_system(rag_system: RAGOrchestrator, preset: ConfigurationPreset):
    apply_chunking_config(rag_system, preset.chunking_config)
    apply_retrieval_config(rag_system, preset.retrieval_config)
    apply_weighting_config(rag_system, preset.weighting_config)
    apply_filter_config(rag_system, preset.filter_config)

def extract_current_config(rag_system: RAGOrchestrator) -> Dict[str, Any]:
    return {
        "chunk_size": getattr(rag_system, 'chunk_size', 1500),
        "chunk_overlap": getattr(rag_system, 'chunk_overlap', 300),
        "chunk_strategy": getattr(rag_system, 'chunk_strategy', 'semantic'),
        "retrieval_k": getattr(rag_system, 'retrieval_k', 6),
        "retrieval_fetch_k": getattr(rag_system, 'retrieval_fetch_k', 25),
        "retrieval_lambda_mult": getattr(rag_system, 'retrieval_lambda_mult', 0.8)
    }

def get_preset_configuration(preset_name: str) -> ConfigurationPreset:
    presets_data = {
        "Default": {
            "description": "Balanced settings for general use",
            "chunking": {"chunk_size": 1500, "chunk_overlap": 300, "chunk_strategy": "semantic", "semantic_threshold": 95},
            "retrieval": {"retrieval_k": 6, "fetch_k": 25, "lambda_mult": 0.8},
            "weighting": {"chapter_match_boost": 1.8, "section_match_boost": 1.5, "pdf_document_boost": 1.2, "early_position_boost": 1.15},
            "filter": {"document_filter": None, "chapter_range": "All", "min_chunk_length": 100}
        },
        "Academic": {
            "description": "Optimized for academic documents",
            "chunking": {"chunk_size": 2000, "chunk_overlap": 400, "chunk_strategy": "semantic", "semantic_threshold": 97},
            "retrieval": {"retrieval_k": 8, "fetch_k": 30, "lambda_mult": 0.9},
            "weighting": {"chapter_match_boost": 2.2, "section_match_boost": 1.8, "pdf_document_boost": 1.4, "early_position_boost": 1.1},
            "filter": {"document_filter": None, "chapter_range": "All", "min_chunk_length": 150}
        },
        "Technical": {
            "description": "Enhanced for technical documentation",
            "chunking": {"chunk_size": 1200, "chunk_overlap": 200, "chunk_strategy": "recursive", "semantic_threshold": None},
            "retrieval": {"retrieval_k": 10, "fetch_k": 40, "lambda_mult": 0.7},
            "weighting": {"chapter_match_boost": 1.5, "section_match_boost": 2.0, "pdf_document_boost": 1.3, "early_position_boost": 1.2},
            "filter": {"document_filter": None, "chapter_range": "All", "min_chunk_length": 50}
        },
        "Creative": {
            "description": "Configured for creative content",
            "chunking": {"chunk_size": 1800, "chunk_overlap": 450, "chunk_strategy": "semantic", "semantic_threshold": 92},
            "retrieval": {"retrieval_k": 5, "fetch_k": 20, "lambda_mult": 0.6},
            "weighting": {"chapter_match_boost": 1.4, "section_match_boost": 1.3, "pdf_document_boost": 1.1, "early_position_boost": 1.3},
            "filter": {"document_filter": None, "chapter_range": "All", "min_chunk_length": 80}
        }
    }
    
    preset_data = presets_data[preset_name]
    
    return ConfigurationPreset(
        name=preset_name,
        description=preset_data["description"],
        chunking_config=ChunkingConfig(**preset_data["chunking"]),
        retrieval_config=RetrievalConfig(**preset_data["retrieval"]),
        weighting_config=WeightingConfig(**preset_data["weighting"]),
        filter_config=FilterConfig(**preset_data["filter"])
    )