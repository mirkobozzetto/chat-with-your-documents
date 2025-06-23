# src/rag_system/document_processor_manager.py
from typing import List, Optional, Callable
from langchain.schema import Document
from langchain_core.language_models import BaseLanguageModel


class DocumentProcessorManager:

    def __init__(self, embeddings, chunk_strategy: str, chunk_size: int, chunk_overlap: int, llm: Optional[BaseLanguageModel] = None, enable_contextual: bool = False):
        if chunk_strategy.startswith("agentic") or chunk_strategy == "hybrid_agentic":
            print(f"🤖 Initializing Agentic Document Processor with strategy: {chunk_strategy}")
            if enable_contextual:
                print("🧠 Contextual RAG enabled with Agentic chunking")
            from src.document_management.agentic_document_processor import AgenticDocumentProcessor
            self.document_processor = AgenticDocumentProcessor(
                embeddings=embeddings,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunk_strategy=chunk_strategy,
                max_workers=4,
                llm=llm,
                enable_contextual=enable_contextual
            )
        else:
            from src.document_management.document_processor import DocumentProcessor
            self.document_processor = DocumentProcessor(
                embeddings=embeddings,
                chunk_strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                llm=llm,
                enable_contextual=enable_contextual
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
        if hasattr(self.document_processor, 'process_documents_agentic'):
            return self.document_processor.process_documents_agentic(documents)
        return self.document_processor.chunk_documents(documents)

    def get_processor_info(self) -> dict:
        return {
            "chunk_strategy": self.chunk_strategy,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }

    def get_document_processor(self):
        return self.document_processor
