# src/auth/auth_manager.py
import bcrypt
import streamlit as st
from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import select
from src.database import get_db_session, User
from .session_persistence import AuthSessionPersistence


class AuthManager:
    def __init__(self):
        self.session_timeout_hours = 24
        self.persistence = AuthSessionPersistence()
        self._restore_session()

    def _restore_session(self) -> None:
        if self.persistence.is_session_valid():
            session_data = self.persistence.get_current_session()
            if session_data:
                st.session_state.authenticated = True
                st.session_state.auth_username = session_data['username']
                st.session_state.auth_timestamp = datetime.fromisoformat(session_data['login_time'])
                print(f"🔐 Restored auth session for: {session_data['username']}")

    def authenticate_user(self, username: str, password: str) -> bool:
        try:
            with next(get_db_session()) as session:
                user = session.exec(select(User).where(User.username == username, User.is_active == True)).first()
                if not user:
                    return False
                return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False

    def is_user_authenticated(self) -> bool:
        if self.persistence.is_session_valid():
            if 'authenticated' not in st.session_state:
                self._restore_session()
            return st.session_state.get('authenticated', False)
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
            if 'auth_username' in st.session_state:
                del st.session_state.auth_username
            if 'auth_timestamp' in st.session_state:
                del st.session_state.auth_timestamp
        return False

    def login_user(self, username: str, password: str) -> bool:
        if self.authenticate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.auth_username = username
            st.session_state.auth_timestamp = datetime.now()
            st.session_state.current_user = {'username': username}
            self.persistence.save_auth_session(username)
            print(f"✅ User logged in: {username}")
            return True
        return False

    def logout_user(self) -> None:
        self.persistence.clear_auth_session()
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        if 'auth_username' in st.session_state:
            del st.session_state.auth_username
        if 'auth_timestamp' in st.session_state:
            del st.session_state.auth_timestamp
        if 'current_user' in st.session_state:
            del st.session_state.current_user

    def get_current_user(self) -> Optional[str]:
        return st.session_state.get('auth_username') if self.is_user_authenticated() else None

    def get_session_info(self) -> Optional[dict]:
        if not self.is_user_authenticated():
            return None

        username = st.session_state.get('auth_username')
        login_time = st.session_state.get('auth_timestamp')

        if login_time:
            expires_at = login_time + timedelta(hours=self.session_timeout_hours)
            time_remaining = expires_at - datetime.now()
        else:
            expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)
            time_remaining = timedelta(hours=self.session_timeout_hours)

        return {
            'username': username,
            'login_time': login_time,
            'expires_at': expires_at,
            'time_remaining': time_remaining,
            'is_valid': self.persistence.is_session_valid()
        }

    def refresh_session(self) -> None:
        if self.is_user_authenticated():
            st.session_state.auth_timestamp = datetime.now()
            session_data = self.persistence.get_current_session()
            if session_data:
                self.persistence.save_auth_session(session_data['username'])

    def get_user_count(self) -> int:
        try:
            from src.database import get_db_session, User
            from sqlmodel import select
            with next(get_db_session()) as session:
                result = session.exec(select(User).where(User.is_active == True))
                return len(list(result))
        except Exception:
            return 0

    def get_current_username(self) -> Optional[str]:
        return self.get_current_user()
