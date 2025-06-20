# RAG Assistant API Documentation

## Overview

The RAG Assistant API is a FastAPI-based REST service that provides programmatic access to a Retrieval-Augmented Generation system. It enables document processing, intelligent querying, conversation management, and agent configuration through HTTP endpoints.

## Architecture

### Core Components

The API maintains the original Streamlit application's architecture while adding enterprise-grade security and isolation:

- **RAGOrchestrator**: Main system orchestrator managing document processing and Q&A
- **User-Isolated Sessions**: Each user gets their own RAG system instance
- **Agent System**: Configurable AI agents with different personalities and behaviors
- **Vector Stores**: Supports both Chroma and Qdrant for document embeddings
- **Authentication**: JWT-based optional authentication system

### Security & Performance

- **User Isolation**: Separate RAG instances prevent cross-user data contamination
- **Rate Limiting**: Multi-tier rate limiting (global, user-specific, endpoint-specific)
- **Quota Management**: Daily request and token limits per user
- **File Validation**: Size limits and type restrictions for uploads
- **Cost Protection**: OpenAI API usage tracking and limits

## API Endpoints

### Authentication

- `POST /api/auth/login` - JWT authentication
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout

### Document Management

- `POST /api/documents/upload` - Upload and process documents (PDF, DOCX, TXT, MD)
- `GET /api/documents/` - List all user documents
- `GET /api/documents/{name}/stats` - Get document statistics
- `POST /api/documents/select` - Select document for queries
- `DELETE /api/documents/select` - Clear document selection
- `DELETE /api/documents/{name}` - Delete document
- `GET /api/documents/stats/knowledge-base` - Knowledge base overview

### Chat & Q&A

- `POST /api/chat/ask` - Ask questions to the RAG system
- `GET /api/chat/conversations` - List conversation history
- `GET /api/chat/conversations/{id}` - Get specific conversation
- `POST /api/chat/conversations` - Create new conversation
- `DELETE /api/chat/conversations/{id}` - Delete conversation

### Agent Configuration

- `GET /api/agents/types` - Available agent types and behaviors
- `POST /api/agents/configure` - Configure agent for document
- `GET /api/agents/` - Agents overview with statistics
- `GET /api/agents/{document}` - Get agent config for document
- `DELETE /api/agents/{document}` - Remove agent configuration
- `PATCH /api/agents/{document}/toggle` - Toggle agent active status

### Debug & Administration

- `POST /api/debug/retrieval/test` - Test retrieval with custom queries
- `GET /api/debug/settings` - Get system settings
- `PATCH /api/debug/settings` - Update retrieval parameters
- `GET /api/debug/vector-store/analysis` - Vector store analysis

### System Information

- `GET /api/system/status` - System operational status
- `GET /api/system/info` - Complete system information
- `GET /api/system/statistics` - Comprehensive usage statistics
- `POST /api/system/cleanup` - Clean old conversations

### Monitoring

- `GET /api/health` - API health check
- `GET /api/info` - API information and rate limits
- `GET /api/quota` - User quota and usage statistics

## Features Implemented

### 1. Complete Functional Parity

All Streamlit application features are available through REST endpoints:

- Document upload and processing with progress tracking
- Multi-format support (PDF, DOCX, TXT, MD)
- Agent configuration with 6 different personalities
- Conversation management and history
- Real-time statistics and monitoring
- Debug tools for retrieval optimization

### 2. User Isolation System

```python
# Each user gets isolated RAG system
def get_user_rag_system(current_user: UserInfo) -> RAGOrchestrator:
    user_id = current_user.username if current_user else "anonymous"
    if user_id not in _user_rag_systems:
        _user_rag_systems[user_id] = RAGOrchestrator(get_rag_config())
    return _user_rag_systems[user_id]
```

### 3. Multi-Tier Rate Limiting

- **Global**: 200 requests/day, 50/hour
- **Authenticated Users**: 100 requests/day, 20/hour
- **Chat Endpoints**: 10 requests/minute
- **File Upload**: 5 uploads/hour
- **Redis Backend**: Supports distributed deployments

### 4. File Security & Validation

```python
# File size and type validation
MAX_FILE_SIZE = 50MB (configurable)
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
```

### 5. OpenAI Cost Protection

```python
# Per-user daily limits
DAILY_REQUEST_LIMIT = 100 requests
DAILY_TOKEN_LIMIT = 50,000 tokens
```

### 6. Agent System

Six pre-configured agent types with distinct behaviors:

- **Conversational**: Natural, accessible responses
- **Technical**: Detailed, precise technical explanations
- **Commercial**: Sales-oriented, persuasive communication
- **Analytical**: Data-driven analysis and comparisons
- **Educational**: Step-by-step learning approach
- **Creative**: Imaginative, innovative responses

## Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Security
JWT_SECRET_KEY=your-secret-key
MAX_FILE_SIZE_MB=50

# Rate Limiting
REDIS_URL=redis://localhost:6379

# Quotas
DAILY_REQUEST_LIMIT=100
DAILY_TOKEN_LIMIT=50000

# OpenAI
OPENAI_API_KEY=your-openai-key
EMBEDDING_MODEL=text-embedding-3-large
CHAT_MODEL=gpt-4.1-2025-04-14

# RAG Configuration
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
CHUNK_STRATEGY=semantic
RETRIEVAL_K=6
```

## Data Models

### Request/Response Models

All endpoints use Pydantic models for validation:

- Type safety and automatic validation
- Comprehensive error messages
- OpenAPI schema generation
- Request/response documentation

### Key Models

- `QuestionRequest/Response`: Chat interactions
- `DocumentUploadResponse`: File processing results
- `AgentConfigRequest/Response`: Agent management
- `ConversationResponse`: Chat history
- `SystemSettingsRequest/Response`: Configuration management

## Usage Examples

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer your-jwt-token" \
  -F "file=@document.pdf"
```

### Ask Question

```bash
curl -X POST "http://localhost:8000/api/chat/ask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "question": "What is the main topic of the document?",
    "document_filter": "document.pdf"
  }'
```

### Configure Agent

```bash
curl -X POST "http://localhost:8000/api/agents/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "document.pdf",
    "agent_type": "technical",
    "custom_instructions": "Focus on technical details",
    "is_active": true
  }'
```

## Security Considerations

### Authentication

- Optional JWT-based authentication
- Configurable user management
- Session persistence and expiration

### Data Isolation

- User-specific RAG systems prevent data leakage
- Separate document collections per user
- Isolated conversation histories

### Resource Protection

- File size limits prevent system overload
- Rate limiting prevents abuse
- Token usage tracking controls OpenAI costs
- Request quotas ensure fair usage

## Deployment

### Requirements

```bash
pip install -r requirements.txt
```

### Starting the API

```bash
# Development
python3 api_server.py

# Production
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Documentation Access

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Migration from Streamlit

The API provides complete functional parity with the Streamlit application:

1. **All Features**: Every Streamlit feature is available via REST endpoints
2. **Same Architecture**: Reuses existing managers and orchestrators
3. **Gradual Migration**: Can run alongside Streamlit app
4. **Enhanced Security**: Adds enterprise-grade security features
5. **Scalability**: Supports horizontal scaling and load balancing

The transition maintains all existing functionality while adding production-ready capabilities for enterprise deployment.
