# src/rag_system/rag_orchestrator.py
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from langchain.schema import Document

from src.vector_stores import VectorStoreFactory
from src.vector_stores.hybrid_search_engine import HybridSearchEngine
from src.rag_system.rank_fusion import RankFusionEngine, ReciprocalRankFusion
from src.rag_system.neural_reranker import NeuralReranker, LightweightReranker
from .ai_service_manager import AIServiceManager
from .document_processor_manager import DocumentProcessorManager
from .document_manager import DocumentManager
from .stats_manager import StatsManager


class RAGOrchestrator:

    def __init__(self, config: Dict[str, Any]):
        print("🚀 Initializing RAG System...")

        self.config = config
        self.enable_contextual_rag = config.get("ENABLE_CONTEXTUAL_RAG", False)
        self._initialize_managers()
        self._initialize_contextual_components()
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
            chunk_overlap=self.config["CHUNK_OVERLAP"],
            llm=self.ai_service_manager.get_llm() if self.enable_contextual_rag else None,
            enable_contextual=self.enable_contextual_rag
        )

        self.vector_store_manager = VectorStoreFactory.create_vector_store_manager(
            embeddings=self.ai_service_manager.get_embeddings()
        )

        from src.document_management import DocumentSelector
        self.document_selector = DocumentSelector(
            vector_store_manager=self.vector_store_manager
        )

        self.document_manager = DocumentManager(
            vector_store_manager=self.vector_store_manager,
            document_selector=self.document_selector
        )

        from src.qa_system import QAManager
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

    def _initialize_contextual_components(self) -> None:
        if self.enable_contextual_rag:
            print("🔧 Initializing Contextual RAG components...")

            self.hybrid_search_engine = HybridSearchEngine(
                vector_store=None,
                dense_weight=self.config.get("DENSE_WEIGHT", 0.6),
                sparse_weight=self.config.get("SPARSE_WEIGHT", 0.4)
            )

            fusion_strategy = ReciprocalRankFusion(k=self.config.get("RRF_K", 60))
            self.rank_fusion_engine = RankFusionEngine(fusion_strategy)

            if self.config.get("USE_NEURAL_RERANKER", True):
                self.reranker = NeuralReranker(
                    llm=self.ai_service_manager.get_llm(),
                    relevance_weight=self.config.get("RELEVANCE_WEIGHT", 0.7),
                    original_weight=self.config.get("ORIGINAL_WEIGHT", 0.3)
                )
            else:
                self.reranker = LightweightReranker()
        else:
            self.hybrid_search_engine = None
            self.rank_fusion_engine = None
            self.reranker = None

    def _initialize_system(self) -> None:
        if self.vector_store_manager.has_documents():
            available_docs = self.document_manager.get_available_documents()
            print(f"✅ Loaded existing knowledge base with {len(available_docs)} documents")

            # Synchronize vector store with restored document selection FIRST
            selected_doc = self.document_manager.get_selected_document()
            if selected_doc and hasattr(self.vector_store_manager, 'set_current_document'):
                self.vector_store_manager.set_current_document(selected_doc)
                print(f"🎯 Synchronized vector store with selected document: {selected_doc}")

            # Create QA chain AFTER synchronization to use correct collection
            self.qa_manager.create_qa_chain()

            # Initialize hybrid search if contextual RAG is enabled
            if self.enable_contextual_rag and self.hybrid_search_engine:
                self._setup_hybrid_search()

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

            # Setup hybrid search for processed document if contextual RAG is enabled
            if self.enable_contextual_rag and self.hybrid_search_engine:
                self._setup_hybrid_search()

            self.stats_manager.print_processing_summary(filename)

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            raise

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if self.enable_contextual_rag:
            return self._contextual_question_answering(question, chat_history)
        else:
            return self.qa_manager.ask_question(question, chat_history)

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        return self.stats_manager.get_knowledge_base_stats()

    def get_available_documents(self) -> List[str]:
        return self.document_manager.get_available_documents()

    def set_selected_document(self, filename: str) -> None:
        self.document_manager.set_selected_document(filename)

        # Synchronize vector store manager with selected document
        if hasattr(self.vector_store_manager, 'set_current_document'):
            self.vector_store_manager.set_current_document(filename)

        # Recreate QA chain to use correct collection
        self.qa_manager.update_document_selection()

    def clear_selected_document(self) -> None:
        self.document_manager.clear_selected_document()

        # Clear vector store manager's current document
        if hasattr(self.vector_store_manager, 'set_current_document'):
            self.vector_store_manager.current_document_filename = None
            self.vector_store_manager.current_collection_name = None

        # Recreate QA chain after clearing selection
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

    def _setup_hybrid_search(self) -> None:
        try:
            vector_store = self.vector_store_manager.get_vector_store()
            if vector_store and self.hybrid_search_engine:
                self.hybrid_search_engine.vector_store = vector_store

                # Get all documents for BM25 indexing
                all_documents = []
                if hasattr(vector_store, '_collection') and vector_store._collection:
                    all_documents = vector_store._collection.get()
                    if all_documents and 'documents' in all_documents:
                        document_objects = [Document(page_content=doc) for doc in all_documents['documents']]
                        self.hybrid_search_engine.index_documents(document_objects)
                        print("✅ Hybrid search engine initialized with BM25 index")
        except Exception as e:
            print(f"⚠️ Failed to setup hybrid search: {e}")

    def _contextual_question_answering(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        try:
            if not self.hybrid_search_engine or not self.rank_fusion_engine or not self.reranker:
                return self.qa_manager.ask_question(question, chat_history)

            # Step 1: Hybrid search
            search_results = self.hybrid_search_engine.hybrid_search(
                query=question,
                k=self.config.get("CONTEXTUAL_RETRIEVAL_K", 20)
            )

            # Step 2: Rank fusion (already done in hybrid search)
            ranked_docs = [(result.document, result.combined_score) for result in search_results]

            # Step 3: Neural reranking
            reranked_results = self.reranker.rerank_documents(
                query=question,
                documents=ranked_docs,
                top_k=self.config.get("FINAL_RETRIEVAL_K", 5)
            )

            # Step 4: Generate answer using reranked documents
            final_docs = [result.document for result in reranked_results]

            # Use QA manager with custom documents
            return self.qa_manager.ask_question_with_documents(question, final_docs, chat_history)

        except Exception as e:
            print(f"⚠️ Contextual RAG failed, falling back to standard RAG: {e}")
            return self.qa_manager.ask_question(question, chat_history)
