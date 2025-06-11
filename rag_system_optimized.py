import os
from typing import List, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

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
    CHROMA_PERSIST_DIRECTORY
)


class OptimizedRAGSystem:
    """RAG System optimisé avec chunking sémantique et derniers modèles OpenAI 2024"""

    def __init__(self):
        """Initialize optimized RAG system with latest models and techniques."""
        print("🚀 Initializing Optimized RAG System...")

        # Initialize OpenAI embeddings - LARGE model for better performance
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,  # text-embedding-3-large
            api_key=OPENAI_API_KEY
        )

        # Initialize OpenAI LLM - Configurable model and temperature
        self.llm = ChatOpenAI(
            model=CHAT_MODEL,  # Configurable via .env
            temperature=CHAT_TEMPERATURE,  # Configurable via .env
            api_key=OPENAI_API_KEY
        )

        # Initialize semantic splitter for intelligent chunking
        if CHUNK_STRATEGY == "semantic":
            print("📚 Using Semantic Chunking Strategy")
            self.text_splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95
            )
        else:
            print("📚 Using Recursive Character Chunking")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

        # Initialize vector store
        self.vector_store = None
        self.qa_chain = None

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Load PDF using PyPDFLoader for better text extraction."""
        print(f"📄 Loading PDF: {pdf_path}")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        print(f"✅ Loaded {len(documents)} pages from PDF")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into optimized chunks."""
        print(f"🔄 Chunking documents with {CHUNK_STRATEGY} strategy...")

        if CHUNK_STRATEGY == "semantic":
            # Combine all documents into one text for semantic chunking
            combined_text = "\n\n".join([doc.page_content for doc in documents])
            chunks = self.text_splitter.create_documents([combined_text])
        else:
            chunks = self.text_splitter.split_documents(documents)

        print(f"✅ Created {len(chunks)} optimized chunks")
        return chunks

    def create_vector_store(self, chunks: List[Document]) -> None:
        """Create and populate vector store."""
        print("🗄️ Creating optimized vector store...")

        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )

        # Add documents in batches for better performance
        batch_size = 50
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"📦 Processing batch {batch_num}/{total_batches}")

            self.vector_store.add_documents(batch)

        print(f"✅ Vector store created with {len(chunks)} chunks")

    def create_qa_chain(self) -> None:
        """Create optimized QA chain with better retrieval."""
        print("🔗 Creating optimized QA chain...")

        retriever = self.vector_store.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={
                "k": RETRIEVAL_K,  # Configurable via .env
                "fetch_k": RETRIEVAL_FETCH_K,  # Configurable via .env
                "lambda_mult": RETRIEVAL_LAMBDA_MULT  # Configurable via .env
            }
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False
        )

        print("✅ QA chain ready")

    def process_pdf(self, pdf_path: str) -> None:
        """Complete pipeline to process PDF."""
        try:
            print(f"\n🎯 Processing PDF with Optimized RAG System")
            print(f"📊 Configuration:")
            print(f"   • Embedding Model: {EMBEDDING_MODEL}")
            print(f"   • Chat Model: {CHAT_MODEL}")
            print(f"   • Chunk Strategy: {CHUNK_STRATEGY}")
            print(f"   • Chunk Size: {CHUNK_SIZE}")
            print(f"   • Chunk Overlap: {CHUNK_OVERLAP}")

            # Load PDF
            documents = self.load_pdf(pdf_path)

            # Chunk documents
            chunks = self.chunk_documents(documents)

            # Create vector store
            self.create_vector_store(chunks)

            # Create QA chain
            self.create_qa_chain()

            print(f"\n🎉 PDF processing complete!")
            print(f"📈 Performance optimizations applied:")
            print(f"   • Latest OpenAI models (2024)")
            print(f"   • {CHUNK_STRATEGY.title()} chunking strategy")
            print(f"   • MMR retrieval for diverse results")
            print(f"   • Batch processing for efficiency")

        except Exception as e:
            print(f"❌ Error processing PDF: {str(e)}")
            raise

    def ask_question(self, question: str) -> dict:
        """Ask question and get optimized answer."""
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Process a PDF first.")

        print(f"\n❓ Question: {question}")
        print("🤔 Thinking...")

        result = self.qa_chain.invoke({"query": question})

        print(f"\n💡 Answer: {result['result']}")
        print(f"\n📚 Sources used: {len(result['source_documents'])} chunks")

        return result

    def get_knowledge_base_stats(self) -> dict:
        """Get statistics about the knowledge base."""
        if not self.vector_store:
            return {"status": "No documents processed"}

        collection = self.vector_store._collection
        count = collection.count()

        return {
            "total_documents": count,
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
