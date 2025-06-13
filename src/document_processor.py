# src/document_processor.py
import os
from typing import List
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

    def load_document(self, file_path: str) -> List[Document]:
        print(f"📄 Loading document: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name

        if file_ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_ext == '.docx':
            loader = UnstructuredWordDocumentLoader(file_path)
        elif file_ext in ['.txt', '.md']:
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported format: {file_ext}")

        documents = loader.load()

        for doc in documents:
            doc.metadata["source_filename"] = filename
            doc.metadata["document_type"] = file_ext[1:]

        print(f"✅ Loaded {len(documents)} sections from document")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        print(f"🔄 Chunking documents with {self.chunk_strategy} strategy...")

        if self.chunk_strategy == "semantic":
            combined_text = "\n\n".join([doc.page_content for doc in documents])
            chunks = self.text_splitter.create_documents([combined_text])
            filename = documents[0].metadata.get("source_filename", "unknown")
            doc_type = documents[0].metadata.get("document_type", "unknown")
            for chunk in chunks:
                chunk.metadata["source_filename"] = filename
                chunk.metadata["document_type"] = doc_type
        else:
            chunks = self.text_splitter.split_documents(documents)

        print(f"✅ Created {len(chunks)} optimized chunks")
        return chunks

    def process_document_pipeline(self, file_path: str) -> List[Document]:
        documents = self.load_document(file_path)
        chunks = self.chunk_documents(documents)
        return chunks
