# src/auth/api_auth_manager.py
import bcrypt
from typing import Optional, Dict, Set
from .auth_config import AuthConfig


class ApiAuthManager:

    def __init__(self):
        self.config = AuthConfig()

    def authenticate_user(self, username: str, password: str) -> bool:
        if not self.config.is_auth_enabled():
            return True

        if not self.config.has_global_access():
            return False

        users = self.config.get_users()
        if username not in users:
            return False

        stored_hash = users[username].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    def is_auth_enabled(self) -> bool:
        return self.config.is_auth_enabled()

    def user_exists(self, username: str) -> bool:
        return self.config.user_exists(username)

    def get_users(self) -> Dict[str, str]:
        return self.config.get_users()

    def get_user_list(self) -> Set[str]:
        return self.config.get_user_list()

    def get_auth_status(self) -> Dict[str, any]:
        return self.config.get_auth_status()
