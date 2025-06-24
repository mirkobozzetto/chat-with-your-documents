# src/ui/session_manager.py
import streamlit as st
import os
from src.rag_system.rag_orchestrator import RAGOrchestrator as RAGSystem
from src.auth import DBAuthManager


class SessionManager:
    """Manages Streamlit session state, authentication and RAG system initialization"""

    def __init__(self):
        self.auth_manager = DBAuthManager()

    def check_authentication(self) -> bool:
        """Check authentication status and redirect if needed"""
        return self.auth_manager.is_user_authenticated()

    def get_current_user(self) -> str:
        """Get currently authenticated user"""
        return self.auth_manager.get_current_username()

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
        if 'rag_system' not in st.session_state:
            with st.spinner("Initializing RAG system..."):
                import config
                rag_config = {
                    "OPENAI_API_KEY": config.OPENAI_API_KEY,
                    "EMBEDDING_MODEL": config.EMBEDDING_MODEL,
                    "CHAT_MODEL": config.CHAT_MODEL,
                    "CHUNK_SIZE": config.CHUNK_SIZE,
                    "CHUNK_OVERLAP": config.CHUNK_OVERLAP,
                    "CHUNK_STRATEGY": config.CHUNK_STRATEGY,
                    "CHAT_TEMPERATURE": config.CHAT_TEMPERATURE,
                    "RETRIEVAL_K": config.RETRIEVAL_K,
                    "RETRIEVAL_FETCH_K": config.RETRIEVAL_FETCH_K,
                    "RETRIEVAL_LAMBDA_MULT": config.RETRIEVAL_LAMBDA_MULT,
                    "VECTOR_STORE_TYPE": config.VECTOR_STORE_TYPE,
                    "ENABLE_CONTEXTUAL_RAG": config.ENABLE_CONTEXTUAL_RAG,
                    "DENSE_WEIGHT": config.DENSE_WEIGHT,
                    "SPARSE_WEIGHT": config.SPARSE_WEIGHT,
                    "RRF_K": config.RRF_K,
                    "USE_NEURAL_RERANKER": config.USE_NEURAL_RERANKER,
                    "RELEVANCE_WEIGHT": config.RELEVANCE_WEIGHT,
                    "ORIGINAL_WEIGHT": config.ORIGINAL_WEIGHT,
                    "CONTEXTUAL_RETRIEVAL_K": config.CONTEXTUAL_RETRIEVAL_K,
                    "FINAL_RETRIEVAL_K": config.FINAL_RETRIEVAL_K
                }
                st.session_state.rag_system = RAGSystem(rag_config)
        return st.session_state.rag_system

    @staticmethod
    def initialize_chat_history() -> list:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages

    @staticmethod
    def clear_chat_history() -> None:
        st.session_state.messages = []
        st.rerun()

    @staticmethod
    def get_rag_system() -> RAGSystem:
        return st.session_state.rag_system

    def get_session_info(self) -> dict:
        auth_info = self.auth_manager.get_session_info()

        if auth_info:
            return {
                "authenticated": True,
                "auth_enabled": True,
                "username": auth_info["username"],
                "login_time": auth_info["login_time"],
                "expires_at": auth_info["expires_at"],
                "time_remaining": auth_info["time_remaining"]
            }
        else:
            return {
                "authenticated": False,
                "auth_enabled": True
            }

    def logout(self) -> None:
        self.auth_manager.logout_user()
        for key in ['rag_system', 'messages']:
            if key in st.session_state:
                del st.session_state[key]
