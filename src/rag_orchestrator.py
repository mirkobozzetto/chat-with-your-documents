# src/rag_orchestrator.py
from typing import List, Dict, Any, Optional, Callable
from langchain.schema import Document

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

from src.rag_system.simple_rag import SimpleRAG


class OptimizedRAGSystem:

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

        self.rag = SimpleRAG(config)

    def load_pdf(self, pdf_path: str) -> List[Document]:
        return self.rag.load_pdf(pdf_path)

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        return self.rag.chunk_documents(documents)

    def create_vector_store(self, chunks: List[Document]):
        self.rag.create_vector_store(chunks)

    def create_qa_chain(self):
        self.rag.create_qa_chain()

    def process_pdf(self, pdf_path: str, progress_callback: Optional[Callable] = None):
        self.rag.process_document(pdf_path, progress_callback)

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return self.rag.ask_question(question, chat_history)

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        return self.rag.get_knowledge_base_stats()

    def get_available_documents(self) -> List[str]:
        return self.rag.get_available_documents()

    def set_selected_document(self, filename: str):
        self.rag.set_selected_document(filename)

    def clear_selected_document(self):
        self.rag.clear_selected_document()

    @property
    def selected_document(self) -> Optional[str]:
        return self.rag.selected_document

    @selected_document.setter
    def selected_document(self, filename: Optional[str]):
        self.rag.selected_document = filename

    def delete_document(self, document_filename: str) -> bool:
        return self.rag.delete_document(document_filename)

    def get_document_info(self, document_filename: str) -> Optional[Dict[str, Any]]:
        return self.rag.get_document_info(document_filename)

    @property
    def qa_manager(self):
        return self.rag.qa_manager

    @property  
    def document_processor(self):
        return self.rag.document_processor
