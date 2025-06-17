# src/auth/session_persistence.py
import json
import streamlit as st
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict


class AuthSessionPersistence:

    def __init__(self, storage_file: str = "auth_sessions.json"):
        self.storage_file = Path(storage_file)
        self.session_timeout_hours = 24

    def _get_browser_session_id(self) -> str:
        if 'persistent_session_id' not in st.session_state:
            import uuid
            st.session_state.persistent_session_id = str(uuid.uuid4())
        return st.session_state.persistent_session_id

    def _load_sessions(self) -> Dict:
        if not self.storage_file.exists():
            return {}

        try:
            with open(self.storage_file, 'r') as f:
                sessions = json.load(f)

            current_time = datetime.now()
            valid_sessions = {}

            for session_id, session_data in sessions.items():
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if expires_at > current_time:
                    valid_sessions[session_id] = session_data

            if len(valid_sessions) != len(sessions):
                self._save_sessions(valid_sessions)

            return valid_sessions
        except Exception as e:
            print(f"Warning: Could not load auth sessions: {e}")
            return {}

    def _save_sessions(self, sessions: Dict) -> None:
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save auth sessions: {e}")

    def save_auth_session(self, username: str) -> None:
        sessions = self._load_sessions()

        for existing_session_id, session_data in list(sessions.items()):
            if session_data.get('username') == username:
                del sessions[existing_session_id]

        browser_session_id = self._get_browser_session_id()
        now = datetime.now()
        expires_at = now + timedelta(hours=self.session_timeout_hours)

        sessions[browser_session_id] = {
            'username': username,
            'login_time': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': now.isoformat()
        }

        self._save_sessions(sessions)

    def get_any_valid_session(self) -> Optional[Dict]:
        sessions = self._load_sessions()

        current_time = datetime.now()

        for session_id, session_data in sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if expires_at > current_time:
                session_data['last_activity'] = current_time.isoformat()
                sessions[session_id] = session_data
                self._save_sessions(sessions)
                return session_data

        return None

    def clear_auth_session(self) -> None:
        sessions = self._load_sessions()
        browser_session_id = self._get_browser_session_id()

        if browser_session_id in sessions:
            del sessions[browser_session_id]
            self._save_sessions(sessions)

    def is_session_valid(self) -> bool:
        session_data = self.get_any_valid_session()
        if not session_data:
            return False

        expires_at = datetime.fromisoformat(session_data['expires_at'])
        return datetime.now() < expires_at
