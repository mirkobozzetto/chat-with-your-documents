# src/api/middleware/rate_limiting.py

from fastapi import Request
from typing import Dict
from datetime import datetime, timedelta

class SimpleRateLimiter:
    """Simple in-memory rate limiter for development"""

    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.window_minutes = 60
        self.max_requests = 100

    def is_allowed(self, user_id: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.window_minutes)

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Record request
        self.requests[user_id].append(now)
        return True

def get_user_identifier(request: Request) -> str:
    """Extract user identifier from request for rate limiting"""
    try:
        from src.api.dependencies.authentication import verify_jwt_token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            username = verify_jwt_token(token)
            if username:
                return f"user:{username}"
    except:
        pass

    # Fallback to IP
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"

class APIRateLimiter:
    def __init__(self):
        self.limiter = SimpleRateLimiter()

    def get_limiter(self):
        return self.limiter

_rate_limiter = APIRateLimiter()

def get_api_rate_limiter():
    """Get the configured rate limiter instance"""
    return _rate_limiter.get_limiter()
