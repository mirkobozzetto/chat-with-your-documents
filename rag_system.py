import os
from typing import List, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
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
    """RAG System optimized with semantic chunking and latest OpenAI models"""

    def __init__(self):
        """Initialize optimized RAG system with latest models and techniques."""
        print("🚀 Initializing Optimized RAG System...")

        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY
        )

        self.llm = ChatOpenAI(
            model=CHAT_MODEL,
            temperature=CHAT_TEMPERATURE,
            api_key=OPENAI_API_KEY
        )

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

        self.vector_store = self._load_existing_vector_store()
        self.qa_chain = None

        if self.vector_store and self._has_documents():
            self.create_qa_chain()
            print(f"✅ Loaded existing knowledge base with {self.get_knowledge_base_stats()['total_documents']} documents")

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """Load document - supports PDF, DOCX, TXT, MD"""
        print(f"📄 Loading document: {pdf_path}")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Document file not found: {pdf_path}")

        file_ext = Path(pdf_path).suffix.lower()

        if file_ext == '.pdf':
            loader = PyPDFLoader(pdf_path)
        elif file_ext == '.docx':
            loader = UnstructuredWordDocumentLoader(pdf_path)
        elif file_ext in ['.txt', '.md']:
            loader = TextLoader(pdf_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported format: {file_ext}")

        documents = loader.load()
        print(f"✅ Loaded {len(documents)} sections from document")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into optimized chunks."""
        print(f"🔄 Chunking documents with {CHUNK_STRATEGY} strategy...")

        if CHUNK_STRATEGY == "semantic":
            combined_text = "\n\n".join([doc.page_content for doc in documents])
            chunks = self.text_splitter.create_documents([combined_text])
        else:
            chunks = self.text_splitter.split_documents(documents)

        print(f"✅ Created {len(chunks)} optimized chunks")
        return chunks

    def _load_existing_vector_store(self):
        """Load existing vector store if available."""
        try:
            if os.path.exists(CHROMA_PERSIST_DIRECTORY):
                vector_store = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory=CHROMA_PERSIST_DIRECTORY
                )
                return vector_store
        except Exception as e:
            print(f"⚠️ Could not load existing vector store: {str(e)}")
        return None

    def _has_documents(self) -> bool:
        """Check if vector store has documents."""
        try:
            if self.vector_store:
                collection = self.vector_store._collection
                return collection.count() > 0
        except:
            return False
        return False

    def create_vector_store(self, chunks: List[Document]) -> None:
        """Create and populate vector store."""
        print("🗄️ Creating optimized vector store...")

        if not self.vector_store:
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIRECTORY
            )

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
            search_type="mmr",
            search_kwargs={
                "k": RETRIEVAL_K,
                "fetch_k": RETRIEVAL_FETCH_K,
                "lambda_mult": RETRIEVAL_LAMBDA_MULT
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
        """Complete pipeline to process document."""
        try:
            print(f"\n🎯 Processing document with Optimized RAG System")
            print(f"📊 Configuration:")
            print(f"   • Embedding Model: {EMBEDDING_MODEL}")
            print(f"   • Chat Model: {CHAT_MODEL}")
            print(f"   • Chunk Strategy: {CHUNK_STRATEGY}")
            print(f"   • Chunk Size: {CHUNK_SIZE}")
            print(f"   • Chunk Overlap: {CHUNK_OVERLAP}")

            documents = self.load_pdf(pdf_path)
            chunks = self.chunk_documents(documents)
            self.create_vector_store(chunks)
            self.create_qa_chain()

            print(f"\n🎉 Document processing complete!")
            print(f"📈 Performance optimizations applied:")
            print(f"   • Latest OpenAI models")
            print(f"   • {CHUNK_STRATEGY.title()} chunking strategy")
            print(f"   • MMR retrieval for diverse results")
            print(f"   • Batch processing for efficiency")

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            raise

    def ask_question(self, question: str, chat_history: list = None) -> dict:
        """Ask question with optional chat history for context."""
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Process a document first.")

        print(f"\n❓ Question: {question}")
        print("🤔 Thinking...")

        if chat_history and len(chat_history) > 0:
            context_messages = []
            for msg in chat_history[-6:]:
                role = "Human" if msg["role"] == "user" else "Assistant"
                context_messages.append(f"{role}: {msg['content']}")

            conversation_context = "\n".join(context_messages)
            enhanced_query = f"""Previous conversation:
{conversation_context}

Current question: {question}

Please answer the current question considering the conversation context above."""

            print("🧠 Using conversation context...")
        else:
            enhanced_query = question

        result = self.qa_chain.invoke({"query": enhanced_query})

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
