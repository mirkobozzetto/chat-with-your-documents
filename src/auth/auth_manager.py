# src/auth/auth_manager.py
import bcrypt
import streamlit as st
from typing import Optional, Dict, Set
from datetime import datetime, timedelta
from .auth_config import AuthConfig


class AuthManager:

    def __init__(self):
        self.config = AuthConfig()
        self.session_timeout_hours = 24

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

    def is_user_authenticated(self) -> bool:
        if not self.config.is_auth_enabled():
            return True

        if 'authenticated' not in st.session_state:
            return False

        if 'auth_timestamp' not in st.session_state:
            return False

        auth_time = st.session_state.auth_timestamp
        if datetime.now() - auth_time > timedelta(hours=self.session_timeout_hours):
            self.logout_user()
            return False

        return st.session_state.authenticated

    def login_user(self, username: str) -> None:
        st.session_state.authenticated = True
        st.session_state.auth_username = username
        st.session_state.auth_timestamp = datetime.now()

    def logout_user(self) -> None:
        for key in ['authenticated', 'auth_username', 'auth_timestamp']:
            if key in st.session_state:
                del st.session_state[key]

    def get_current_user(self) -> Optional[str]:
        if self.is_user_authenticated():
            return st.session_state.get('auth_username')
        return None

    def get_authenticated_users(self) -> Set[str]:
        return self.config.get_user_list()

    def refresh_session(self) -> None:
        if self.is_user_authenticated():
            st.session_state.auth_timestamp = datetime.now()

    def get_session_info(self) -> Dict[str, any]:
        if not self.is_user_authenticated():
            return {"authenticated": False}

        auth_time = st.session_state.auth_timestamp
        expires_at = auth_time + timedelta(hours=self.session_timeout_hours)

        return {
            "authenticated": True,
            "username": self.get_current_user(),
            "login_time": auth_time,
            "expires_at": expires_at,
            "time_remaining": expires_at - datetime.now()
        }
