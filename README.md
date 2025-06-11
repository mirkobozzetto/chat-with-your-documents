# RAG AI Assistant - Chat with your documents

A modern RAG (Retrieval-Augmented Generation) system using OpenAI for embeddings and chat, with an intuitive Streamlit interface.

## Features

- **PDF Upload**: Automatic PDF document processing
- **Intelligent Chunking**: Optimized document segmentation with semantic chunking
- **Web Interface**: Modern and responsive Streamlit interface
- **Local Vector Store**: Persistent ChromaDB database
- **Source Citations**: Display of passages used for responses

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
python cli.py path/to/your/document.pdf
python3 cli.py path/to/your/document.pdf
```

## Architecture

```
rag-ai/
├── app.py                    # Streamlit interface
├── rag_system_optimized.py   # Optimized RAG system
├── config.py                 # Configuration
├── cli.py              # Command line demo
├── requirements.txt         # Dependencies
└── chroma_db/              # Vector database (auto-created)
```

## Technical Stack

- **LangChain**: RAG framework with experimental semantic chunking
- **OpenAI**: Latest embeddings (text-embedding-3-large) + Chat (gpt-4.1-2025-04-14)
- **ChromaDB**: Local vector store
- **Streamlit**: Web interface
- **PyPDF**: PDF parser
- **Sentence Transformers**: For semantic chunking

## Configuration

All settings are now configurable via environment variables in your `.env` file:

**Chunking Options:**

- `CHUNK_STRATEGY`: semantic (recommended) or recursive
- `CHUNK_SIZE`: Size of each chunk (tokens for semantic, characters for recursive)
- `CHUNK_OVERLAP`: Overlap between chunks

**Performance Tuning:**

- `CHAT_TEMPERATURE`: Creativity level (0.0-2.0)
- `RETRIEVAL_K`: Number of chunks to retrieve
- `RETRIEVAL_FETCH_K`: Number of candidates to consider
- `RETRIEVAL_LAMBDA_MULT`: Balance between relevance and diversity

## Quick Start

1. Launch the app: `streamlit run app.py`
2. Upload a PDF in the sidebar
3. Click "Process PDF"
4. Ask questions in the chat

## Key Dependencies

- `langchain>=0.1.0`: RAG framework
- `langchain-openai>=0.1.0`: OpenAI integration
- `langchain-experimental>=0.1.0`: Semantic chunking
- `chromadb>=0.4.0`: Vector database
- `streamlit>=1.31.0`: Web interface
- `sentence-transformers>=2.5.0`: Enhanced embeddings
