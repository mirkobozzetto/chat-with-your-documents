# src/rag_system/stats_manager.py
from typing import Dict, Any
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from .document_manager import DocumentManager
from .ai_service_manager import AIServiceManager
from .document_processor_manager import DocumentProcessorManager


class StatsManager:
    """
    Generates system statistics and knowledge base information
    """

    def __init__(self, vector_store_manager: BaseVectorStoreManager,
                 document_manager: DocumentManager,
                 ai_service_manager: AIServiceManager,
                 doc_processor_manager: DocumentProcessorManager,
                 vector_store_type: str,
                 retrieval_config: Dict[str, Any]):
        self.vector_store_manager = vector_store_manager
        self.document_manager = document_manager
        self.ai_service_manager = ai_service_manager
        self.doc_processor_manager = doc_processor_manager
        self.vector_store_type = vector_store_type
        self.retrieval_config = retrieval_config

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        if not self.vector_store_manager.get_vector_store():
            return {"status": "No documents processed"}

        chunk_count = self.vector_store_manager.get_chunk_count()
        doc_stats = self.document_manager.get_document_stats()
        ai_info = self.ai_service_manager.get_service_info()
        processor_info = self.doc_processor_manager.get_processor_info()

        stats = {
            "total_documents": doc_stats["total_documents"],
            "total_chunks": chunk_count,
            "available_documents": doc_stats["available_documents"],
            "selected_document": doc_stats["selected_document"],
            "vector_store_type": self.vector_store_type,
            **ai_info,
            **processor_info,
            **self.retrieval_config
        }

        if hasattr(self.vector_store_manager, 'get_connection_info'):
            stats["connection_info"] = self.vector_store_manager.get_connection_info()

        return stats

    def get_system_configuration(self) -> Dict[str, Any]:
        return {
            "vector_store": self.vector_store_type,
            "ai_services": self.ai_service_manager.get_service_info(),
            "document_processing": self.doc_processor_manager.get_processor_info(),
            "retrieval": self.retrieval_config
        }

    def print_processing_summary(self, filename: str) -> None:
        config = self.get_system_configuration()

        print(f"\n🎉 Document processing complete!")
        print(f"📈 Performance optimizations applied:")
        print(f"   • Latest OpenAI models")
        print(f"   • {config['document_processing']['chunk_strategy'].title()} chunking strategy")
        print(f"   • MMR retrieval for diverse results")
        print(f"   • {config['vector_store'].upper()} vector store with per-document collections")
