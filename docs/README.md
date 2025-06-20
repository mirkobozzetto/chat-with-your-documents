# RAG Assistant - Documentation

This directory contains comprehensive documentation for the RAG Assistant system.

## Available Documentation

### [API Documentation](./api-documentation.md)

Complete guide to the FastAPI REST service including:

- Architecture overview and security features
- Complete endpoint reference
- Configuration and deployment instructions
- Usage examples and code samples
- Migration guide from Streamlit

## Quick Start

### Streamlit Application

```bash
pip install -r requirements.txt
streamlit run app.py
```

### FastAPI Service

```bash
pip install -r requirements.txt
python3 api_server.py
```

### API Documentation Access

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Key Features

- **Document Processing**: PDF, DOCX, TXT, MD support
- **Intelligent Q&A**: RAG-powered question answering
- **Agent System**: 6 configurable AI personalities
- **User Isolation**: Secure multi-user support
- **Rate Limiting**: Production-ready request controls
- **Cost Protection**: OpenAI usage quotas and monitoring

## Architecture

Both Streamlit and FastAPI implementations share the same core architecture:

- RAGOrchestrator for system coordination
- Modular agent and vector store management
- Conversation history and session management
- Configurable retrieval and generation parameters
