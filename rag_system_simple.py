import os
from typing import List, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.schema import Document

from config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHROMA_PERSIST_DIRECTORY
)


class SimpleRAGSystem:
    """RAG System using PyPDF (no OCR, text-only PDFs)"""

    def __init__(self):
        """Initialize the RAG system with OpenAI embeddings and Chroma vector store."""
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY
        )

        self.llm = ChatOpenAI(
            model=CHAT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize or load vector store
        self.vector_store = self._init_vector_store()

    def _init_vector_store(self) -> Chroma:
        """Initialize or load existing Chroma vector store."""
        persist_dir = CHROMA_PERSIST_DIRECTORY + "_simple"

        if os.path.exists(persist_dir):
            return Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )
        else:
            return Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Load and parse PDF document using PyPDF (text-only)."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        print(f"Loaded {len(documents)} pages from {pdf_path}")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        return chunks

    def add_documents_to_vectorstore(self, chunks: List[Document]) -> None:
        """Add document chunks to vector store."""
        self.vector_store.add_documents(chunks)
        # Persistence is automatic in langchain-chroma
        print(f"Added {len(chunks)} chunks to vector store")

    def process_pdf(self, pdf_path: str) -> None:
        """Complete pipeline: load PDF, chunk, and add to vector store."""
        documents = self.load_pdf(pdf_path)
        chunks = self.chunk_documents(documents)
        self.add_documents_to_vectorstore(chunks)

    def create_qa_chain(self) -> RetrievalQA:
        """Create question-answering chain."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        return qa_chain

    def query(self, question: str) -> dict:
        """Query the RAG system."""
        qa_chain = self.create_qa_chain()
        result = qa_chain.invoke({"query": question})

        return {
            "answer": result["result"],
            "source_documents": result["source_documents"]
        }

    def get_collection_stats(self) -> dict:
        """Get statistics about the vector store collection."""
        collection = self.vector_store._collection
        return {
            "total_documents": collection.count(),
            "collection_name": collection.name
        }
