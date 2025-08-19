# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG system for document Q&A using OpenAI. Multi-user authentication, PostgreSQL persistence, dual vector store options (Qdrant/ChromaDB).

## Development Commands

### Local Development

```bash
# Start PostgreSQL + run Streamlit locally
make dev

# Stop all services
make down

# Force rebuild for code changes
make rebuild

# Clean everything (nuclear option)
make clean
```

### Testing

```bash
# Run authentication system tests
uv run test_auth_system.py

# Test smart presets functionality
uv run test_smart_presets.py
```

### Linting & Type Checking

```bash
# Python linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/
```

### Docker Commands

```bash
# Build containers
make build

# Start full stack
make up

# Initialize database (uses python in container)
make init-db

# Create user (uses python in container)
make create-user USER=admin PASS=admin123

# Run database migrations
make migrate-auth
```

**Note**: Docker containers use standard `python`, not `uv`. To use `uv` in Docker, use `docker-compose.uv.yml` with `Dockerfile.uv`.

### Running Components Individually

```bash
# Streamlit UI
uv run streamlit run app.py

# API Server
uv run api_server.py

# CLI
uv run cli.py path/to/document.pdf
```

## Architecture Overview

### Component Locations

- **API Server**: `api_server.py` (full feature API), `api/index.py` (Vercel serverless)
- **Streamlit UI**: `app.py` (main entry point)
- **CLI Interface**: `cli.py` (command-line document processing)
- **Quality Gates**: `src/quality/` (document and chunk validation)
- **Vector Stores**: `src/vector_stores/` (Qdrant/ChromaDB implementations)
- **Authentication**: `src/auth/` (user management, JWT tokens)
- **RAG Pipeline**: `src/qa_system/` (Q&A orchestration)
- **Document Processing**: `src/document_management/` (chunking, processing)
- **Database Models**: `src/database/` (PostgreSQL models)
- **API Models**: `src/api/models/` (Pydantic models)

### Core Flow

1. **Document Processing**: Upload → Extract metadata → Chunk → Generate embeddings → Store in vector DB
2. **Query Processing**: User question → Vector search → Context expansion → LLM generation → Response with sources
3. **Storage**: PostgreSQL for users/conversations (JSONB), Vector stores for embeddings

### Key Architectural Decisions

- **PostgreSQL with JSONB**: Flexible schema for conversations and metadata
- **User Isolation**: Each user gets isolated RAG instances (`user_{user_id}_{doc_name}` collections)
- **Dual Vector Store**: Factory pattern for Qdrant/ChromaDB
- **Authentication Layers**: Streamlit session-based, API JWT tokens

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    session_id VARCHAR UNIQUE NOT NULL,
    user_id VARCHAR REFERENCES users(id),
    title VARCHAR,
    messages JSONB DEFAULT '[]',
    extra_data JSONB DEFAULT '{}',
    document_name VARCHAR,
    agent_type VARCHAR,
    tags JSONB DEFAULT '[]',
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Configuration

Required in `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx

# Vector Store
VECTOR_STORE_TYPE=qdrant  # or chroma
QDRANT_URL=https://...
QDRANT_API_KEY=xxx

# PostgreSQL (for Docker)
POSTGRES_DB=chat_with_your_documents
POSTGRES_USER=chat_with_your_documents
POSTGRES_PASSWORD=letsgo

# Optional
AUTH_ENABLED=true
CHUNK_STRATEGY=semantic  # or recursive
```

## Code Organization Patterns

### Mappers for Data Transformation

Located in `src/mappers/`:
- `conversation_mappers.py`: Conversation object transformations
- `api_mappers.py`: API response formatting
- `db_mappers.py`: Database model conversions

### Storage Abstraction

- Interface: `ConversationStorage` (abstract base)
- Implementations: `PostgresConversationStorage`, `JSONConversationStorage`
- Located in: `src/chat_history/storage/`

### Component Structure

UI components follow MVC pattern:
- Controllers: `src/ui/controllers/` (orchestration)
- Components: `src/ui/components/` (UI elements)
- Adapters: Bridge between systems

## Quality Gate System

Validates documents before vectorization:

### Configuration

```python
from src.quality.document_quality_gate import DocumentQualityGate

quality_gate = DocumentQualityGate(
    min_score_threshold=0.6,
    enable_empirical_validation=False
)
```

### Quality Metrics

- **Semantic Coherence**: Content meaning consistency
- **Size Consistency**: Chunk size uniformity
- **Overlap Quality**: Appropriate chunk overlap
- **Information Density**: Content richness
- **Content Density**: Text vs whitespace ratio

### Validation Process

```python
is_valid, result = quality_gate.validate_before_vectorization(chunks, document_path)
if not is_valid:
    print(result.rejection_reasons)
    print(result.recommendations)
```

## Common Tasks

### Adding a New Vector Store

1. Extend `VectorStoreBase` in `src/vector_stores/base.py`
2. Implement required methods: `add_documents`, `similarity_search`, `delete`
3. Add to factory in `src/vector_stores/factory.py`

### Adding a New Agent Type

1. Add to `AgentTypeEnum` in `src/api/models/agents.py`
2. Update agent prompts in `src/agents/agent_prompts.py`
3. Add UI option in `src/ui/components/agent_configuration.py`

### Debugging Database Issues

```bash
# Connect to PostgreSQL
docker exec -it chat-with-your-documents-postgres-1 psql -U chat_with_your_documents

# Common queries
\dt  -- List tables
\d conversations  -- Show table structure
SELECT * FROM users;
SELECT session_id, title, message_count FROM conversations;
```

## Testing Approach

### Automated Tests

```bash
# Test authentication system
uv run test_auth_system.py

# Test smart presets
uv run test_smart_presets.py
```

### Manual Testing Workflow

1. `make dev` - Start local development
2. Login with admin/admin123
3. Upload test document
4. Ask questions to verify RAG pipeline
5. Check PostgreSQL for conversation persistence
6. Test API endpoints at http://localhost:8000/docs

### Quality Gate Testing

1. Upload a low-quality document (many images, little text)
2. Verify quality gate rejection with scores
3. Upload high-quality document
4. Verify quality gate approval

## Performance Considerations

- **Chunk Size**: Balance between context (larger) and precision (smaller)
- **Embedding Cache**: Reuse embeddings for same documents
- **Batch Processing**: Vector stores process in batches of 100
- **Connection Pooling**: PostgreSQL uses SQLModel's connection management
- **Session Cleanup**: Old sessions expire after 24 hours

## Security Notes

- Passwords hashed with bcrypt (12 rounds)
- File validation prevents malicious uploads
- User isolation at database and vector store level
- JWT tokens for API authentication
- Environment variables for secrets (never commit .env)

## API Deployment Options

### Vercel Deployment (Serverless)

```bash
# Basic deployment
vercel deploy

# Production deployment
vercel deploy --prod
```

**Vercel Files:**
- `vercel.json` - Configuration (Python 3.12, 30s timeout)
- `api/index.py` - Minimal RAG API
- `requirements-vercel.txt` - Minimal dependencies

### Full API Server

```bash
# Complete API with all features
uv run api_server.py
# Access Swagger docs at http://localhost:8000/docs
```

## Custom Qdrant Client

The system includes a custom Qdrant HTTP client (`src/vector_stores/custom_qdrant_client.py`) that:
- Forces IPv4 connections to avoid IPv6 issues
- Handles SSL verification and timeouts
- Provides better error messages
- Implements retry logic

## LangGraph Migration

### Quick Setup

```bash
# Install LangGraph
uv pip install langgraph==0.2.16 langgraph-checkpoint-postgres==2.0.2

# Enable in environment
echo "ENABLE_LANGGRAPH=true" >> .env
```

### Architecture

LangGraph integrates cleanly in `src/langgraph/`:
- Wraps existing components (no duplication)
- Feature flag controlled
- Maintains backward compatibility

See `LANGGRAPH_MIGRATION.md` for implementation details.