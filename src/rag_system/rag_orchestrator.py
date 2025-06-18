# src/rag_system/rag_orchestrator.py
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from langchain.schema import Document

from src.vector_stores import VectorStoreFactory
from src.qa_manager import QAManager
from .ai_service_manager import AIServiceManager
from .document_processor_manager import DocumentProcessorManager
from .document_manager import DocumentManager
from .stats_manager import StatsManager


class RAGOrchestrator:
    """
    Orchestrates the complete RAG system by coordinating all components
    """

    def __init__(self, config: Dict[str, Any]):
        print("🚀 Initializing RAG System...")

        self.config = config
        self._initialize_managers()
        self._initialize_system()

    def _initialize_managers(self) -> None:
        self.ai_service_manager = AIServiceManager(
            openai_api_key=self.config["OPENAI_API_KEY"],
            embedding_model=self.config["EMBEDDING_MODEL"],
            chat_model=self.config["CHAT_MODEL"],
            chat_temperature=self.config["CHAT_TEMPERATURE"]
        )

        self.doc_processor_manager = DocumentProcessorManager(
            embeddings=self.ai_service_manager.get_embeddings(),
            chunk_strategy=self.config["CHUNK_STRATEGY"],
            chunk_size=self.config["CHUNK_SIZE"],
            chunk_overlap=self.config["CHUNK_OVERLAP"]
        )

        self.vector_store_manager = VectorStoreFactory.create_vector_store_manager(
            embeddings=self.ai_service_manager.get_embeddings()
        )

        from src.document_selector import DocumentSelector
        self.document_selector = DocumentSelector(
            vector_store_manager=self.vector_store_manager
        )

        self.document_manager = DocumentManager(
            vector_store_manager=self.vector_store_manager,
            document_selector=self.document_selector
        )

        self.qa_manager = QAManager(
            llm=self.ai_service_manager.get_llm(),
            vector_store_manager=self.vector_store_manager,
            document_selector=self.document_selector,
            retrieval_k=self.config["RETRIEVAL_K"],
            retrieval_fetch_k=self.config["RETRIEVAL_FETCH_K"],
            retrieval_lambda_mult=self.config["RETRIEVAL_LAMBDA_MULT"]
        )

        self.stats_manager = StatsManager(
            vector_store_manager=self.vector_store_manager,
            document_manager=self.document_manager,
            ai_service_manager=self.ai_service_manager,
            doc_processor_manager=self.doc_processor_manager,
            vector_store_type=self.config["VECTOR_STORE_TYPE"],
            retrieval_config={
                "retrieval_k": self.config["RETRIEVAL_K"],
                "retrieval_fetch_k": self.config["RETRIEVAL_FETCH_K"],
                "retrieval_lambda_mult": self.config["RETRIEVAL_LAMBDA_MULT"]
            }
        )

    def _initialize_system(self) -> None:
        if self.vector_store_manager.has_documents():
            self.qa_manager.create_qa_chain()
            available_docs = self.document_manager.get_available_documents()
            print(f"✅ Loaded existing knowledge base with {len(available_docs)} documents")

    def process_document(self, pdf_path: str, progress_callback: Optional[Callable] = None) -> None:
        try:
            filename = Path(pdf_path).name

            if hasattr(self.vector_store_manager, 'set_current_document'):
                self.vector_store_manager.set_current_document(filename)

            chunks = self.doc_processor_manager.process_document_pipeline(
                pdf_path, filename, progress_callback
            )

            self.vector_store_manager.create_vector_store(chunks, progress_callback)

            self.document_manager.finalize_document_processing(filename)

            self.qa_manager.create_qa_chain()

            self.stats_manager.print_processing_summary(filename)

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            raise

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return self.qa_manager.ask_question(question, chat_history)

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        return self.stats_manager.get_knowledge_base_stats()

    def get_available_documents(self) -> List[str]:
        return self.document_manager.get_available_documents()

    def set_selected_document(self, filename: str) -> None:
        self.document_manager.set_selected_document(filename)
        self.qa_manager.update_document_selection()

    def clear_selected_document(self) -> None:
        self.document_manager.clear_selected_document()
        self.qa_manager.update_document_selection()

    @property
    def selected_document(self) -> Optional[str]:
        return self.document_manager.get_selected_document()

    @selected_document.setter
    def selected_document(self, filename: Optional[str]) -> None:
        if filename is None:
            self.clear_selected_document()
        else:
            self.set_selected_document(filename)

    def delete_document(self, document_filename: str) -> bool:
        success = self.document_manager.delete_document(document_filename)

        if success:
            remaining_docs = self.document_manager.get_available_documents()
            if remaining_docs:
                self.qa_manager.create_qa_chain()

        return success

    def get_document_info(self, document_filename: str) -> Optional[Dict[str, Any]]:
        return self.document_manager.get_document_info(document_filename)

    def load_pdf(self, pdf_path: str) -> List[Document]:
        return self.doc_processor_manager.load_document(pdf_path)

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        return self.doc_processor_manager.chunk_documents(documents)

    def create_vector_store(self, chunks: List[Document]) -> None:
        self.vector_store_manager.create_vector_store(chunks)

    def create_qa_chain(self) -> None:
        self.qa_manager.create_qa_chain()

    def process_pdf(self, pdf_path: str, progress_callback: Optional[Callable] = None) -> None:
        self.process_document(pdf_path, progress_callback)
