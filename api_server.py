#!/usr/bin/env python3

# api_server.py

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import Optional
import uvicorn
import os

from src.api.routers import (
    auth_router,
    chat_router,
    documents_router,
    agents_router,
    debug_router,
    system_router
)
from src.api.dependencies import get_optional_current_user
from src.api.models.auth_models import UserInfo

app = FastAPI(
    title="RAG Assistant API",
    description="Professional REST API for Retrieval-Augmented Generation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(agents_router)
app.include_router(debug_router)
app.include_router(system_router)

@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "RAG Assistant API is operational",
        "version": "1.0.0"
    }

@app.get("/api/info")
async def api_information():
    return {
        "name": "RAG Assistant API",
        "version": "1.0.0",
        "description": "Professional RAG system API with FastAPI",
        "endpoints": {
            "auth": "/api/auth/*",
            "chat": "/api/chat/*",
            "documents": "/api/documents/*",
            "agents": "/api/agents/*",
            "debug": "/api/debug/*",
            "system": "/api/system/*",
            "quota": "/api/quota",
            "docs": "/docs"
        },
        "supported_formats": ["PDF", "DOCX", "TXT", "MD"],
        "vector_stores": ["Chroma", "Qdrant"],
        "features": [
            "User-isolated RAG systems",
            "File validation and quotas",
            "JWT authentication",
            "Agent configuration",
            "Conversation management"
        ]
    }

@app.get("/api/quota")
async def get_user_quota_info(
    current_user: Optional[UserInfo] = Depends(get_optional_current_user)
):
    try:
        from src.api.middleware import get_quota_manager
        quota_manager = get_quota_manager()

        user_id = current_user.username if current_user else "anonymous"
        usage_stats = quota_manager.get_usage_stats(user_id)

        return {
            "user_id": user_id,
            "usage": usage_stats,
            "limits": {
                "file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
                "daily_requests": usage_stats["daily_request_limit"],
                "daily_tokens": usage_stats["daily_token_limit"]
            }
        }
    except ImportError:
        return {
            "user_id": current_user.username if current_user else "anonymous",
            "usage": {"requests_today": 0, "tokens_today": 0},
            "limits": {
                "file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
                "daily_requests": 100,
                "daily_tokens": 50000
            }
        }

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    print(f"Starting RAG Assistant API on {host}:{port}")
    print(f"Documentation: http://{host}:{port}/docs")

    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
