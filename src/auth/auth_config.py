# src/auth/auth_config.py
import os
import json
import bcrypt
from typing import Dict, Set
from pathlib import Path


class AuthConfig:

    def __init__(self):
        self.auth_file_path = "auth_users.json"
        self.sync_users_from_env()

    def is_auth_enabled(self) -> bool:
        return os.getenv("AUTH_ENABLED", "false").lower() == "true"

    def has_global_access(self) -> bool:
        return os.getenv("AUTH_GLOBAL_ACCESS", "true").lower() == "true"

    def get_users_from_env(self) -> Dict[str, str]:
        auth_users_env = os.getenv("AUTH_USERS", "")
        if not auth_users_env:
            return {}

        users = {}
        for user_pass in auth_users_env.split(","):
            if ":" in user_pass:
                username, password = user_pass.split(":", 1)
                users[username.strip()] = password.strip()
        return users

    def load_stored_users(self) -> Dict[str, str]:
        if not Path(self.auth_file_path).exists():
            return {}

        try:
            with open(self.auth_file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_users(self, users: Dict[str, str]) -> None:
        with open(self.auth_file_path, 'w') as f:
            json.dump(users, f, indent=2)

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def sync_users_from_env(self) -> None:
        if not self.is_auth_enabled():
            return

        env_users = self.get_users_from_env()
        stored_users = self.load_stored_users()

        updated_users = {}

        for username, plain_password in env_users.items():
            if username in stored_users:
                updated_users[username] = stored_users[username]
            else:
                updated_users[username] = self.hash_password(plain_password)

        if updated_users != stored_users:
            self.save_users(updated_users)

    def get_users(self) -> Dict[str, str]:
        return self.load_stored_users()

    def get_user_list(self) -> Set[str]:
        return set(self.get_users().keys())

    def user_exists(self, username: str) -> bool:
        return username in self.get_users()

    def get_auth_status(self) -> Dict[str, any]:
        return {
            "auth_enabled": self.is_auth_enabled(),
            "global_access": self.has_global_access(),
            "total_users": len(self.get_users()),
            "configured_users": list(self.get_user_list())
        }
