# src/rag_system/optimized_rag_system.py
from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNK_STRATEGY,
    CHAT_TEMPERATURE,
    RETRIEVAL_K,
    RETRIEVAL_FETCH_K,
    RETRIEVAL_LAMBDA_MULT,
    VECTOR_STORE_TYPE
)

from .rag_orchestrator import RAGOrchestrator


class OptimizedRAGSystem(RAGOrchestrator):

    def __init__(self):
        config = {
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "EMBEDDING_MODEL": EMBEDDING_MODEL,
            "CHAT_MODEL": CHAT_MODEL,
            "CHUNK_SIZE": CHUNK_SIZE,
            "CHUNK_OVERLAP": CHUNK_OVERLAP,
            "CHUNK_STRATEGY": CHUNK_STRATEGY,
            "CHAT_TEMPERATURE": CHAT_TEMPERATURE,
            "RETRIEVAL_K": RETRIEVAL_K,
            "RETRIEVAL_FETCH_K": RETRIEVAL_FETCH_K,
            "RETRIEVAL_LAMBDA_MULT": RETRIEVAL_LAMBDA_MULT,
            "VECTOR_STORE_TYPE": VECTOR_STORE_TYPE
        }

        super().__init__(config)

        self.qa_manager.retrieval_k = RETRIEVAL_K
        self.qa_manager.retrieval_fetch_k = RETRIEVAL_FETCH_K
        self.qa_manager.retrieval_lambda_mult = RETRIEVAL_LAMBDA_MULT

    @property
    def document_processor(self):
        return self.doc_processor_manager.get_document_processor()
