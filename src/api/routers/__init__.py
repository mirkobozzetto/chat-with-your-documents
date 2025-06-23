# src/api/routers/__init__.py
from .auth import router as auth_router
from .chat import router as chat_router
from .documents import router as documents_router
from .agents import router as agents_router
from .debug import router as debug_router
from .system import router as system_router
from .advanced import router as advanced_router


__all__ = ["auth_router", "chat_router", "documents_router", "agents_router", "debug_router", "system_router", "advanced_router"]
