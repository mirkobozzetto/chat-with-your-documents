# src/auth/auth_manager.py
import bcrypt
import streamlit as st
from typing import Optional, Dict, Set
from datetime import datetime, timedelta
from .auth_config import AuthConfig
from .session_persistence import AuthSessionPersistence


class AuthManager:

    def __init__(self):
        self.config = AuthConfig()
        self.session_timeout_hours = 24
        self.persistence = AuthSessionPersistence()
        self._restore_session()

    def _restore_session(self) -> None:
        if self.persistence.is_session_valid():
            session_data = self.persistence.get_any_valid_session()
            if session_data:
                st.session_state.authenticated = True
                st.session_state.auth_username = session_data['username']
                st.session_state.auth_timestamp = datetime.fromisoformat(session_data['login_time'])
                print(f"🔐 Restored auth session for: {session_data['username']}")

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

        if self.persistence.is_session_valid():
            if 'authenticated' not in st.session_state:
                self._restore_session()
            return st.session_state.get('authenticated', False)

        if 'authenticated' in st.session_state:
            auth_time = st.session_state.get('auth_timestamp')
            if auth_time and datetime.now() - auth_time > timedelta(hours=self.session_timeout_hours):
                self.logout_user()
                return False
            return st.session_state.authenticated

        return False

    def login_user(self, username: str) -> None:
        now = datetime.now()
        st.session_state.authenticated = True
        st.session_state.auth_username = username
        st.session_state.auth_timestamp = now

        self.persistence.save_auth_session(username)

    def logout_user(self) -> None:
        self.persistence.clear_auth_session()

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
            session_data = self.persistence.get_any_valid_session()
            if session_data:
                self.persistence.save_auth_session(session_data['username'])

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
