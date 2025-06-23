# src/services/config_service.py
from typing import Dict, Any
from src.rag_system.rag_orchestrator import RAGOrchestrator


class ConfigService:
    """
    Service responsible for managing and applying configurations.
    Handles RAG system configuration.
    """

    def apply_chunking_config(self, rag_system: RAGOrchestrator, config: Dict[str, Any]) -> None:
        rag_system.chunk_size = config["chunk_size"]
        rag_system.chunk_overlap = config["chunk_overlap"]
        rag_system.chunk_strategy = config["chunk_strategy"]

        if hasattr(rag_system, 'document_processor_manager'):
            rag_system.document_processor_manager.chunk_strategy = config["chunk_strategy"]
            rag_system.document_processor_manager.chunk_size = config["chunk_size"]
            rag_system.document_processor_manager.chunk_overlap = config["chunk_overlap"]

        if config.get("enable_contextual_rag"):
            rag_system.enable_contextual_rag = True
            if hasattr(rag_system, 'hybrid_search_engine') and rag_system.hybrid_search_engine:
                rag_system.hybrid_search_engine.set_weights(
                    config.get("dense_weight", 0.6),
                    config.get("sparse_weight", 0.4)
                )
            if hasattr(rag_system, 'reranker') and hasattr(rag_system.reranker, 'set_weights'):
                rag_system.reranker.set_weights(
                    config.get("relevance_weight", 0.7),
                    config.get("original_weight", 0.3)
                )

    def apply_retrieval_config(self, rag_system: RAGOrchestrator, config: Dict[str, Any]) -> None:
        rag_system.qa_manager.retrieval_k = config["retrieval_k"]
        rag_system.qa_manager.retrieval_fetch_k = config["fetch_k"]
        rag_system.qa_manager.retrieval_lambda_mult = config["lambda_mult"]
        rag_system.qa_manager.create_qa_chain()

    def apply_weighting_config(self, rag_system: RAGOrchestrator, config: Dict[str, Any]) -> None:
        if hasattr(rag_system, 'vector_store_manager'):
            vector_store = rag_system.vector_store_manager.get_vector_store()
            if hasattr(vector_store, 'search_engine'):
                search_engine = vector_store.search_engine
                search_engine.chapter_match_boost = config["chapter_match_boost"]
                search_engine.section_match_boost = config["section_match_boost"]
                search_engine.pdf_document_boost = config["pdf_document_boost"]
                search_engine.early_position_boost = config["early_position_boost"]

    def apply_filter_config(self, rag_system: RAGOrchestrator, config: Dict[str, Any]) -> None:
        if config["document_filter"]:
            for doc in config["document_filter"]:
                rag_system.set_selected_document(doc)
        rag_system.min_chunk_length = config["min_chunk_length"]

    def apply_preset_config(self, rag_system: RAGOrchestrator, preset_config: Dict[str, Any]) -> None:
        print(f"🎛️ Applying preset configuration: {preset_config}")

        chunking_config = {
            "chunk_size": preset_config.get("chunk_size", 1500),
            "chunk_overlap": preset_config.get("chunk_overlap", 300),
            "chunk_strategy": preset_config.get("chunk_strategy", "semantic")
        }
        self.apply_chunking_config(rag_system, chunking_config)

        retrieval_config = {
            "retrieval_k": preset_config.get("retrieval_k", 6),
            "fetch_k": preset_config.get("fetch_k", 25),
            "lambda_mult": preset_config.get("lambda_mult", 0.8)
        }
        self.apply_retrieval_config(rag_system, retrieval_config)

        weighting_config = {
            "chapter_match_boost": preset_config.get("chapter_match_boost", 1.8),
            "section_match_boost": preset_config.get("section_match_boost", 1.5),
            "pdf_document_boost": preset_config.get("pdf_document_boost", 1.2),
            "early_position_boost": preset_config.get("early_position_boost", 1.15)
        }
        self.apply_weighting_config(rag_system, weighting_config)

        print("✅ Preset configuration applied successfully")
