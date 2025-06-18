# src/rag_orchestrator.py
from typing import List, Dict, Any, Optional, Callable
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

    def process_pdf(self, pdf_path: str, progress_callback: Optional[Callable] = None) -> None:
        try:
            filename = Path(pdf_path).name
            print(f"\n🎯 Processing document with Optimized RAG System: {filename}")
            print(f"📊 Configuration:")
            print(f"   • Vector Store: {VECTOR_STORE_TYPE.upper()}")
            print(f"   • Embedding Model: {EMBEDDING_MODEL}")
            print(f"   • Chat Model: {CHAT_MODEL}")
            print(f"   • Chunk Strategy: {CHUNK_STRATEGY}")
            print(f"   • Chunk Size: {CHUNK_SIZE}")
            print(f"   • Chunk Overlap: {CHUNK_OVERLAP}")

            # Set current document for vector store manager
            if hasattr(self.vector_store_manager, 'set_current_document'):
                self.vector_store_manager.set_current_document(filename)

            chunks = self.document_processor.process_document_pipeline(pdf_path, progress_callback)
            self.vector_store_manager.create_vector_store(chunks, progress_callback)

            time.sleep(1)

            available_docs = self.document_selector.get_available_documents()
            print(f"📚 Available documents after processing: {available_docs}")

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
            print(f"   • {VECTOR_STORE_TYPE.upper()} vector store with per-document collections")

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

    def delete_document(self, document_filename: str) -> bool:
        """Delete a document and all its chunks from the vector store"""
        try:
            print(f"🗑️ Deleting document: {document_filename}")

            # Check if document exists (get fresh data)
            available_docs = self.get_available_documents()
            if document_filename not in available_docs:
                print(f"❌ Document not found: {document_filename}")
                return False

            # Clear selection if deleting selected document
            if self.selected_document == document_filename:
                self.clear_selected_document()

            # Delete from vector store
            success = self.vector_store_manager.delete_document(document_filename)

            if success:
                # Force refresh of available documents after deletion
                print(f"🔄 Forcing refresh of document list...")
                
                # Get updated document list
                remaining_docs = self.get_available_documents()
                print(f"📋 Documents after deletion: {remaining_docs}")
                
                if remaining_docs:
                    self.qa_manager.create_qa_chain()
                    print(f"✅ Document deleted successfully. {len(remaining_docs)} documents remaining.")
                else:
                    print(f"✅ Document deleted. Knowledge base is now empty.")
                    
                # Clear any cached document selection persistence if document was deleted
                if document_filename not in remaining_docs:
                    self.document_selector.persistence.clear_selection()
                    
            else:
                print(f"❌ Failed to delete document: {document_filename}")

            return success

        except Exception as e:
            print(f"❌ Error deleting document {document_filename}: {str(e)}")
            return False

    def get_document_info(self, document_filename: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific document"""
        try:
            available_docs = self.get_available_documents()
            if document_filename not in available_docs:
                return None

            chunk_count = self.vector_store_manager.get_document_chunk_count(document_filename)

            # Get metadata for this document
            all_metadata = self.vector_store_manager.get_all_metadata()
            doc_metadata = [m for m in all_metadata if m.get('source_filename') == document_filename]

            # Calculate stats
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

        except Exception as e:
            print(f"⚠️ Error getting document info for {document_filename}: {str(e)}")
            return None
