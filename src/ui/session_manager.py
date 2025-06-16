# src/ui/session_manager.py
import streamlit as st
import os
from rag_system import OptimizedRAGSystem as RAGSystem
from src.auth import AuthManager


class SessionManager:
    """Manages Streamlit session state, authentication and RAG system initialization"""

    def __init__(self):
        self.auth_manager = AuthManager()

    def check_authentication(self) -> bool:
        """Check authentication status and redirect if needed"""
        return self.auth_manager.is_user_authenticated()

    def get_current_user(self) -> str:
        """Get currently authenticated user"""
        return self.auth_manager.get_current_user()

    @staticmethod
    def check_api_key() -> bool:
        """Check if OpenAI API key is available"""
        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ OPENAI_API_KEY not found in environment variables!")
            st.markdown("Please set your OpenAI API key in a `.env` file:")
            st.code("OPENAI_API_KEY=your_api_key_here")
            return False
        return True

    @staticmethod
    def initialize_rag_system() -> RAGSystem:
        """Initialize RAG system with caching"""
        if 'rag_system' not in st.session_state:
            with st.spinner("Initializing RAG system..."):
                st.session_state.rag_system = RAGSystem()
        return st.session_state.rag_system

    @staticmethod
    def initialize_chat_history() -> list:
        """Initialize chat history if not exists"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages

    @staticmethod
    def clear_chat_history() -> None:
        """Clear chat history and rerun"""
        st.session_state.messages = []
        st.rerun()

    @staticmethod
    def get_rag_system() -> RAGSystem:
        """Get current RAG system instance"""
        return st.session_state.rag_system

    def get_session_info(self) -> dict:
        """Get complete session information"""
        auth_info = self.auth_manager.get_session_info()

        session_info = {
            "authenticated": auth_info["authenticated"],
            "auth_enabled": self.auth_manager.config.is_auth_enabled()
        }

        if auth_info["authenticated"]:
            session_info.update({
                "username": auth_info["username"],
                "login_time": auth_info["login_time"],
                "expires_at": auth_info["expires_at"],
                "time_remaining": auth_info["time_remaining"]
            })

        return session_info

    def logout(self) -> None:
        """Logout user and clear session"""
        self.auth_manager.logout_user()
        # Clear RAG system and other session data
        for key in ['rag_system', 'messages']:
            if key in st.session_state:
                del st.session_state[key]
