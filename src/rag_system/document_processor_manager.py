# src/rag_system/document_processor_manager.py
import time
from typing import List, Optional, Callable
from pathlib import Path
from langchain.schema import Document
from src.document_management import DocumentProcessor


class DocumentProcessorManager:
    """
    Manages document processing pipeline and coordination
    """

    def __init__(self, embeddings, chunk_strategy: str, chunk_size: int, chunk_overlap: int):
        self.document_processor = DocumentProcessor(
            embeddings=embeddings,
            chunk_strategy=chunk_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        self.chunk_strategy = chunk_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_document_pipeline(self, pdf_path: str, filename: str,
                                progress_callback: Optional[Callable] = None) -> List[Document]:

        print(f"\n🎯 Processing document: {filename}")
        print(f"📊 Processing configuration:")
        print(f"   • Chunk Strategy: {self.chunk_strategy}")
        print(f"   • Chunk Size: {self.chunk_size}")
        print(f"   • Chunk Overlap: {self.chunk_overlap}")

        chunks = self.document_processor.process_document_pipeline(pdf_path, progress_callback)

        print(f"✅ Document processing complete: {len(chunks)} chunks created")
        return chunks

    def load_document(self, pdf_path: str) -> List[Document]:
        return self.document_processor.load_document(pdf_path)

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        return self.document_processor.chunk_documents(documents)

    def get_processor_info(self) -> dict:
        return {
            "chunk_strategy": self.chunk_strategy,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
