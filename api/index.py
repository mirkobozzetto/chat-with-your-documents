"""
Vercel Serverless API Entry Point
Minimal RAG API for deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

# Import existing components from src
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="RAG API",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    question: str
    collection_name: Optional[str] = None
    k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: list
    confidence: float

@app.get("/")
async def root():
    return {"status": "ready", "docs": "/docs"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "qdrant": bool(os.getenv("QDRANT_URL"))
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process RAG query"""
    try:
        # Use existing RAG system
        from src.rag_system.rag_orchestrator import RAGOrchestrator
        from src.services.config_service import ConfigService

        config = ConfigService.get_config()
        rag = RAGOrchestrator(config)

        result = rag.process_query(
            question=request.question,
            collection_name=request.collection_name,
            k=request.k
        )

        return QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel handler
handler = app
