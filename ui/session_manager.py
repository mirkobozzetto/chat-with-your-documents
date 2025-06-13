# ui/session_manager.py
import streamlit as st
import os
from rag_system import OptimizedRAGSystem as RAGSystem


class SessionManager:
    """Manages Streamlit session state and RAG system initialization"""

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
