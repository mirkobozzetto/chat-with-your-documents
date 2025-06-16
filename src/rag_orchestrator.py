# src/rag_orchestrator.py
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import time

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

from src.document_processor import DocumentProcessor
from src.vector_stores import VectorStoreFactory
from src.document_selector import DocumentSelector
from src.qa_manager import QAManager


class OptimizedRAGSystem:

    def __init__(self):
        print("🚀 Initializing Optimized RAG System...")

        self._initialize_ai_services()
        self._initialize_components()
        self._initialize_system()

    def _initialize_ai_services(self):
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY
        )

        self.llm = ChatOpenAI(
            model=CHAT_MODEL,
            temperature=CHAT_TEMPERATURE,
            api_key=OPENAI_API_KEY
        )

    def _initialize_components(self):
        self.document_processor = DocumentProcessor(
            embeddings=self.embeddings,
            chunk_strategy=CHUNK_STRATEGY,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        self.vector_store_manager = VectorStoreFactory.create_vector_store_manager(
            embeddings=self.embeddings
        )

        self.document_selector = DocumentSelector(
            vector_store_manager=self.vector_store_manager
        )

        self.qa_manager = QAManager(
            llm=self.llm,
            vector_store_manager=self.vector_store_manager,
            document_selector=self.document_selector,
            retrieval_k=RETRIEVAL_K,
            retrieval_fetch_k=RETRIEVAL_FETCH_K,
            retrieval_lambda_mult=RETRIEVAL_LAMBDA_MULT
        )

    def _initialize_system(self):
        if self.vector_store_manager.has_documents():
            self.qa_manager.create_qa_chain()
            available_docs = self.document_selector.get_available_documents()
            print(f"✅ Loaded existing knowledge base with {len(available_docs)} documents")

    def load_pdf(self, pdf_path: str) -> List:
        return self.document_processor.load_document(pdf_path)

    def chunk_documents(self, documents: List) -> List:
        return self.document_processor.chunk_documents(documents)

    def create_vector_store(self, chunks: List) -> None:
        self.vector_store_manager.create_vector_store(chunks)

    def create_qa_chain(self) -> None:
        self.qa_manager.create_qa_chain()

    def process_pdf(self, pdf_path: str) -> None:
        try:
            print(f"\n🎯 Processing document with Optimized RAG System")
            print(f"📊 Configuration:")
            print(f"   • Vector Store: {VECTOR_STORE_TYPE.upper()}")
            print(f"   • Embedding Model: {EMBEDDING_MODEL}")
            print(f"   • Chat Model: {CHAT_MODEL}")
            print(f"   • Chunk Strategy: {CHUNK_STRATEGY}")
            print(f"   • Chunk Size: {CHUNK_SIZE}")
            print(f"   • Chunk Overlap: {CHUNK_OVERLAP}")

            chunks = self.document_processor.process_document_pipeline(pdf_path)
            self.vector_store_manager.create_vector_store(chunks)

            time.sleep(1)

            available_docs = self.document_selector.get_available_documents()
            print(f"📚 Available documents after processing: {available_docs}")

            filename = Path(pdf_path).name
            if filename not in available_docs:
                print(f"⚠️ Document {filename} not yet available, waiting...")
                time.sleep(2)
                available_docs = self.document_selector.get_available_documents()
                print(f"📚 Available documents after wait: {available_docs}")

            self.document_selector.set_selected_document(filename)
            self.qa_manager.create_qa_chain()

            print(f"\n🎉 Document processing complete!")
            print(f"📈 Performance optimizations applied:")
            print(f"   • Latest OpenAI models")
            print(f"   • {CHUNK_STRATEGY.title()} chunking strategy")
            print(f"   • MMR retrieval for diverse results")
            print(f"   • {VECTOR_STORE_TYPE.upper()} vector store")

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            raise

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return self.qa_manager.ask_question(question, chat_history)

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        if not self.vector_store_manager.get_vector_store():
            return {"status": "No documents processed"}

        chunk_count = self.vector_store_manager.get_chunk_count()
        doc_stats = self.document_selector.get_document_stats()

        stats = {
            "total_documents": doc_stats["total_documents"],
            "total_chunks": chunk_count,
            "available_documents": doc_stats["available_documents"],
            "selected_document": doc_stats["selected_document"],
            "vector_store_type": VECTOR_STORE_TYPE,
            "embedding_model": EMBEDDING_MODEL,
            "chat_model": CHAT_MODEL,
            "chunk_strategy": CHUNK_STRATEGY,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "chat_temperature": CHAT_TEMPERATURE,
            "retrieval_k": RETRIEVAL_K,
            "retrieval_fetch_k": RETRIEVAL_FETCH_K,
            "retrieval_lambda_mult": RETRIEVAL_LAMBDA_MULT
        }

        if hasattr(self.vector_store_manager, 'get_connection_info'):
            stats["connection_info"] = self.vector_store_manager.get_connection_info()

        return stats

    def get_available_documents(self) -> List[str]:
        return self.document_selector.get_available_documents()

    def set_selected_document(self, filename: str) -> None:
        self.document_selector.set_selected_document(filename)
        self.qa_manager.update_document_selection()

    def clear_selected_document(self) -> None:
        self.document_selector.clear_selected_document()
        self.qa_manager.update_document_selection()

    @property
    def selected_document(self) -> Optional[str]:
        return self.document_selector.get_selected_document()

    @selected_document.setter
    def selected_document(self, filename: Optional[str]) -> None:
        if filename is None:
            self.clear_selected_document()
        else:
            self.set_selected_document(filename)
