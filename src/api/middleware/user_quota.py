# src/api/middleware/user_quota.py

from typing import Dict
from datetime import datetime
from fastapi import HTTPException, status
import os

class UserQuotaManager:
    def __init__(self):
        self.daily_request_limit = int(os.getenv("DAILY_REQUEST_LIMIT", "100"))
        self.daily_token_limit = int(os.getenv("DAILY_TOKEN_LIMIT", "50000"))
        self.user_usage: Dict[str, Dict] = {}

    def _get_user_usage(self, user_id: str) -> Dict:
        """Get or initialize user usage data"""
        if user_id not in self.user_usage:
            self.user_usage[user_id] = {
                "requests_today": 0,
                "tokens_today": 0,
                "last_reset": datetime.now().date()
            }

        usage = self.user_usage[user_id]
        # Reset daily counters if date changed
        if usage["last_reset"] < datetime.now().date():
            usage["requests_today"] = 0
            usage["tokens_today"] = 0
            usage["last_reset"] = datetime.now().date()

        return usage

    def check_request_quota(self, user_id: str) -> None:
        """Check if user can make another request"""
        usage = self._get_user_usage(user_id)
        if usage["requests_today"] >= self.daily_request_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily request limit exceeded ({self.daily_request_limit} requests/day)"
            )

    def check_token_quota(self, user_id: str, estimated_tokens: int) -> None:
        """Check if user can use the estimated tokens"""
        usage = self._get_user_usage(user_id)
        if usage["tokens_today"] + estimated_tokens > self.daily_token_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily token limit would be exceeded. Used: {usage['tokens_today']}, Limit: {self.daily_token_limit}"
            )

    def record_usage(self, user_id: str, tokens_used: int = 0) -> None:
        """Record actual usage for a user"""
        usage = self._get_user_usage(user_id)
        usage["requests_today"] += 1
        usage["tokens_today"] += tokens_used

    def get_usage_stats(self, user_id: str) -> Dict:
        """Get current usage statistics for a user"""
        usage = self._get_user_usage(user_id)
        return {
            "requests_today": usage["requests_today"],
            "tokens_today": usage["tokens_today"],
            "daily_request_limit": self.daily_request_limit,
            "daily_token_limit": self.daily_token_limit,
            "requests_remaining": max(0, self.daily_request_limit - usage["requests_today"]),
            "tokens_remaining": max(0, self.daily_token_limit - usage["tokens_today"])
        }

_quota_manager = UserQuotaManager()

def get_quota_manager() -> UserQuotaManager:
    """Get the global quota manager instance"""
    return _quota_manager
