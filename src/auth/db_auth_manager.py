# src/auth/db_auth_manager.py
import bcrypt
import streamlit as st
from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import select

from src.database import get_db_session, User
from .session_persistence import AuthSessionPersistence


class DBAuthManager:

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
                user = session.exec(
                    select(User).where(User.username == username, User.is_active == True)
                ).first()

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
            timestamp = st.session_state.get('auth_timestamp')
            if timestamp and (datetime.now() - timestamp) < timedelta(hours=self.session_timeout_hours):
                return True

        return False

    def login_user(self, username: str) -> None:
        login_time = datetime.now()
        st.session_state.authenticated = True
        st.session_state.auth_username = username
        st.session_state.auth_timestamp = login_time

        self.persistence.create_session(username, login_time)
        print(f"✅ User logged in: {username}")

    def logout_user(self) -> None:
        username = st.session_state.get('auth_username', 'unknown')

        for key in ['authenticated', 'auth_username', 'auth_timestamp']:
            if key in st.session_state:
                del st.session_state[key]

        self.persistence.clear_sessions()
        print(f"👋 User logged out: {username}")

    def get_current_username(self) -> Optional[str]:
        if self.is_user_authenticated():
            return st.session_state.get('auth_username')
        return None

    def get_session_info(self) -> Optional[dict]:
        if not self.is_user_authenticated():
            return None

        timestamp = st.session_state.get('auth_timestamp')
        if not timestamp:
            return None

        time_remaining = timedelta(hours=self.session_timeout_hours) - (datetime.now() - timestamp)

        return {
            'username': st.session_state.get('auth_username'),
            'login_time': timestamp,
            'time_remaining': time_remaining,
            'expires_at': timestamp + timedelta(hours=self.session_timeout_hours)
        }

    def get_user_count(self) -> int:
        try:
            with next(get_db_session()) as session:
                result = session.exec(select(User).where(User.is_active == True))
                return len(list(result))
        except Exception:
            return 0

    def refresh_session(self) -> None:
        if self.is_user_authenticated():
            st.session_state.auth_timestamp = datetime.now()
            session_data = self.persistence.get_current_session()
            if session_data:
                self.persistence.save_auth_session(session_data['username'])
