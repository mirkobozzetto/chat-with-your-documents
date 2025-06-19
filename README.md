# RAG AI Assistant - Chat with your documents

A modern RAG (Retrieval-Augmented Generation) system using OpenAI for embeddings and chat

## Features

- **Multi-format Documents**: PDF, DOCX, TXT, Markdown processing with metadata extraction
- **Advanced Chunking**: Semantic or recursive chunking with automatic chapter/section detection
- **Intelligent Retrieval**: Context expansion with adjacent chunks and weighted scoring
- **Dual Vector Stores**: Qdrant (cloud or self-hosted) or ChromaDB (local) with per-document collections
- **AI Agents**: 6 specialized agent types configurable per document with custom instructions
- **Chapter-Aware Search**: Automatic detection and filtering of chapter-specific queries
- **Authentication**: Optional user management with session persistence
- **Chat History**: Persistent conversations with UUID-based session management
- **Source Citations**: Detailed passage tracking with chapter and metadata references

## Installation

**Install dependencies:**

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

### Command Line

```bash
# Windows
python cli.py path/to/your/document.pdf

# Linux or macOS
python3 cli.py path/to/your/document.pdf
```

## Technical Stack

- **LangChain**: RAG framework with experimental semantic chunking
- **OpenAI**: Latest embeddings (text-embedding-3-large) + Chat (gpt-4.1-2025-04-14)
- **Vector Stores**: Qdrant (cloud) or ChromaDB (local) with factory pattern
- **Authentication**: bcrypt-based user management (optional)
- **Streamlit**: Web interface with modular components
- **Custom Qdrant Client**: Direct HTTP client for better reliability

## Configuration

All settings are configurable via environment variables in your `.env` file:

**Vector Store Options:**

- `VECTOR_STORE_TYPE`: `qdrant` (cloud) or `chroma` (local)
- `QDRANT_URL` + `QDRANT_API_KEY`: For Qdrant setup

**AI Models:**

- `CHAT_MODEL`: OpenAI chat model (default: gpt-4.1-2025-04-14)
- `EMBEDDING_MODEL`: Embedding model (default: text-embedding-3-large)

**Document Processing:**

- `CHUNK_STRATEGY`: `semantic` (recommended) or `recursive`
- `CHUNK_OVERLAP`: Overlap between chunks

**Authentication (Optional):**

- `AUTH_ENABLED`: Enable user authentication
- `AUTH_USERS`: User credentials in format `user:pass,user2:pass2`

**Performance Tuning:**

- `CHAT_TEMPERATURE`: Creativity level (0.0-2.0)
- `RETRIEVAL_K`: Number of chunks to retrieve
- `RETRIEVAL_FETCH_K`: Number of candidates to consider

## Quick Start

1. Copy `.env.example` to `.env` and configure your API keys
2. Choose vector store: Qdrant (production) or ChromaDB (local)
3. Launch: `streamlit run app.py`
4. Upload documents and start chatting

## Key Dependencies

- `langchain>=0.1.0`: RAG framework
- `langchain-openai>=0.1.0`: OpenAI integration
- `langchain-qdrant>=0.1.0`: Qdrant vector store
- `chromadb>=0.4.0`: Local vector database
- `streamlit>=1.31.0`: Web interface
- `sentence-transformers>=2.5.0`: Enhanced embeddings
- `bcrypt>=4.0.0`: Authentication
