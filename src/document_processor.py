# src/document_processor.py
import os
import concurrent.futures
from typing import List, Callable, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.schema import Document


class DocumentProcessor:

    def __init__(self, embeddings, chunk_strategy: str, chunk_size: int, chunk_overlap: int):
        self.embeddings = embeddings
        self.chunk_strategy = chunk_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_workers = 4

        if chunk_strategy == "semantic":
            print("📚 Using Semantic Chunking Strategy")
            self.text_splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95
            )
        else:
            print("📚 Using Recursive Character Chunking")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

    def load_document(self, file_path: str, progress_callback: Optional[Callable] = None) -> List[Document]:
        print(f"📄 Loading document: {file_path}")

        if progress_callback:
            progress_callback(0.1, "Loading document...")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name

        loaders = {
            '.pdf': lambda: PyPDFLoader(file_path),
            '.docx': lambda: UnstructuredWordDocumentLoader(file_path),
            '.txt': lambda: TextLoader(file_path, encoding='utf-8'),
            '.md': lambda: TextLoader(file_path, encoding='utf-8')
        }

        if file_ext not in loaders:
            raise ValueError(f"Unsupported format: {file_ext}")

        loader = loaders[file_ext]()

        if progress_callback:
            progress_callback(0.3, "Extracting text...")

        documents = loader.load()

        for doc in documents:
            doc.metadata["source_filename"] = filename
            doc.metadata["document_type"] = file_ext[1:]

        if progress_callback:
            progress_callback(0.5, f"Loaded {len(documents)} sections")

        print(f"✅ Loaded {len(documents)} sections from document")
        return documents

    def chunk_documents(self, documents: List[Document], progress_callback: Optional[Callable] = None) -> List[Document]:
        print(f"🔄 Chunking documents with {self.chunk_strategy} strategy...")

        if progress_callback:
            progress_callback(0.6, "Chunking documents...")

        if self.chunk_strategy == "semantic":
            combined_text = "\n\n".join([doc.page_content for doc in documents])
            chunks = self.text_splitter.create_documents([combined_text])

            filename = documents[0].metadata.get("source_filename", "unknown")
            doc_type = documents[0].metadata.get("document_type", "unknown")

            for chunk in chunks:
                chunk.metadata["source_filename"] = filename
                chunk.metadata["document_type"] = doc_type
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                chunk_futures = []

                batch_size = max(1, len(documents) // self.max_workers)
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    future = executor.submit(self.text_splitter.split_documents, batch)
                    chunk_futures.append(future)

                chunks = []
                for future in concurrent.futures.as_completed(chunk_futures):
                    chunks.extend(future.result())

        if progress_callback:
            progress_callback(0.8, f"Created {len(chunks)} chunks")

        print(f"✅ Created {len(chunks)} optimized chunks")
        return chunks

    def process_document_pipeline(self, file_path: str, progress_callback: Optional[Callable] = None) -> List[Document]:
        if progress_callback:
            progress_callback(0.05, "Starting processing...")

        documents = self.load_document(file_path, progress_callback)
        chunks = self.chunk_documents(documents, progress_callback)

        if progress_callback:
            progress_callback(0.9, "Processing complete!")

        return chunks

    def estimate_processing_time(self, file_size_mb: float) -> str:
        if file_size_mb < 1:
            return "~10 seconds"
        elif file_size_mb < 5:
            return "~30 seconds"
        elif file_size_mb < 20:
            return "~1-2 minutes"
        elif file_size_mb < 100:
            return "~3-5 minutes"
        else:
            return "~5-10 minutes"
