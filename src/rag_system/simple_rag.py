# src/rag_system/simple_rag.py
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from src.vector_stores import VectorStoreFactory
from src.document_processor import DocumentProcessor
from src.document_selector import DocumentSelector
from src.qa_manager import QAManager


class SimpleRAG:

    def __init__(self, config: Dict[str, Any]):
        print("🚀 Initializing RAG System...")

        self.config = config
        self._init_services()
        self._init_components()
        self._init_system()

    def _init_services(self):
        self.embeddings = OpenAIEmbeddings(
            model=self.config["EMBEDDING_MODEL"],
            api_key=self.config["OPENAI_API_KEY"]
        )

        self.llm = ChatOpenAI(
            model=self.config["CHAT_MODEL"],
            temperature=self.config["CHAT_TEMPERATURE"],
            api_key=self.config["OPENAI_API_KEY"]
        )

    def _init_components(self):
        self.document_processor = DocumentProcessor(
            embeddings=self.embeddings,
            chunk_strategy=self.config["CHUNK_STRATEGY"],
            chunk_size=self.config["CHUNK_SIZE"],
            chunk_overlap=self.config["CHUNK_OVERLAP"]
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
            retrieval_k=self.config["RETRIEVAL_K"],
            retrieval_fetch_k=self.config["RETRIEVAL_FETCH_K"],
            retrieval_lambda_mult=self.config["RETRIEVAL_LAMBDA_MULT"]
        )
        
        # Expose retrieval settings for debug sidebar
        self.qa_manager.retrieval_k = self.config["RETRIEVAL_K"]
        self.qa_manager.retrieval_fetch_k = self.config["RETRIEVAL_FETCH_K"] 
        self.qa_manager.retrieval_lambda_mult = self.config["RETRIEVAL_LAMBDA_MULT"]

    def _init_system(self):
        if self.vector_store_manager.has_documents():
            available_docs = self.document_selector.get_available_documents()
            
            # Set current document if one is selected
            selected_doc = self.document_selector.get_selected_document()
            if selected_doc and hasattr(self.vector_store_manager, 'set_current_document'):
                self.vector_store_manager.set_current_document(selected_doc)
                print(f"📄 Set current document: {selected_doc}")
            
            self.qa_manager.create_qa_chain()
            print(f"✅ Loaded existing knowledge base with {len(available_docs)} documents")

    def process_document(self, pdf_path: str, progress_callback: Optional[Callable] = None):
        filename = Path(pdf_path).name

        if hasattr(self.vector_store_manager, 'set_current_document'):
            self.vector_store_manager.set_current_document(filename)

        chunks = self.document_processor.process_document_pipeline(pdf_path, progress_callback)
        self.vector_store_manager.create_vector_store(chunks, progress_callback)

        available_docs = self.document_selector.get_available_documents()
        if filename in available_docs:
            self.document_selector.set_selected_document(filename)

        self.qa_manager.create_qa_chain()

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
            "vector_store_type": self.config["VECTOR_STORE_TYPE"],
            "embedding_model": self.config["EMBEDDING_MODEL"],
            "chat_model": self.config["CHAT_MODEL"],
            "chunk_strategy": self.config["CHUNK_STRATEGY"],
            "chunk_size": self.config["CHUNK_SIZE"],
            "chunk_overlap": self.config["CHUNK_OVERLAP"],
            "chat_temperature": self.config["CHAT_TEMPERATURE"],
            "retrieval_k": self.config["RETRIEVAL_K"],
            "retrieval_fetch_k": self.config["RETRIEVAL_FETCH_K"],
            "retrieval_lambda_mult": self.config["RETRIEVAL_LAMBDA_MULT"]
        }

        if hasattr(self.vector_store_manager, 'get_connection_info'):
            stats["connection_info"] = self.vector_store_manager.get_connection_info()

        return stats

    def get_available_documents(self) -> List[str]:
        return self.document_selector.get_available_documents()

    def set_selected_document(self, filename: str):
        self.document_selector.set_selected_document(filename)
        
        # Update current document for vector store manager
        if hasattr(self.vector_store_manager, 'set_current_document'):
            self.vector_store_manager.set_current_document(filename)
            
        self.qa_manager.update_document_selection()

    def clear_selected_document(self):
        self.document_selector.clear_selected_document()
        self.qa_manager.update_document_selection()

    @property
    def selected_document(self) -> Optional[str]:
        return self.document_selector.get_selected_document()

    @selected_document.setter
    def selected_document(self, filename: Optional[str]):
        if filename is None:
            self.clear_selected_document()
        else:
            self.set_selected_document(filename)

    def delete_document(self, document_filename: str) -> bool:
        available_docs = self.get_available_documents()
        if document_filename not in available_docs:
            return False

        if self.selected_document == document_filename:
            self.clear_selected_document()

        success = self.vector_store_manager.delete_document(document_filename)

        if success:
            remaining_docs = self.get_available_documents()
            if remaining_docs:
                self.qa_manager.create_qa_chain()
            if document_filename not in remaining_docs:
                self.document_selector.persistence.clear_selection()

        return success

    def get_document_info(self, document_filename: str) -> Optional[Dict[str, Any]]:
        available_docs = self.get_available_documents()
        if document_filename not in available_docs:
            return None

        chunk_count = self.vector_store_manager.get_document_chunk_count(document_filename)
        all_metadata = self.vector_store_manager.get_all_metadata()
        doc_metadata = [m for m in all_metadata if m.get('source_filename') == document_filename]

        chapters = set()
        sections = set()
        total_words = 0

        for meta in doc_metadata:
            if meta.get('chapter_number'):
                chapters.add(meta['chapter_number'])
            if meta.get('section_number'):
                sections.add(meta['section_number'])
            total_words += meta.get('word_count', 0)

        return {
            "filename": document_filename,
            "chunk_count": chunk_count,
            "total_words": total_words,
            "chapters": sorted(list(chapters)),
            "sections": sorted(list(sections)),
            "document_type": doc_metadata[0].get('document_type', 'unknown') if doc_metadata else 'unknown'
        }

    # Legacy API
    def load_pdf(self, pdf_path: str) -> List[Document]:
        return self.document_processor.load_document(pdf_path)

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        return self.document_processor.chunk_documents(documents)

    def create_vector_store(self, chunks: List[Document]):
        self.vector_store_manager.create_vector_store(chunks)

    def create_qa_chain(self):
        self.qa_manager.create_qa_chain()

    def process_pdf(self, pdf_path: str, progress_callback: Optional[Callable] = None):
        self.process_document(pdf_path, progress_callback)
