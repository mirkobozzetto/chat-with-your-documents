# app.py
import streamlit as st
from src.ui.session_manager import SessionManager
from src.ui.components import DocumentManagement, KnowledgeBaseStats, ChatInterface


def setup_page_config():
    st.set_page_config(
        page_title="RAG AI Assistant",
        page_icon="🤖",
        layout="wide"
    )


def render_page_header():
    st.title("🤖 RAG AI Assistant")
    st.markdown("Upload documents and ask questions about their content using OpenAI embeddings.")


def render_sidebar(rag_system):
    with st.sidebar:
        DocumentManagement.render_upload_section(rag_system)
        DocumentManagement.render_selection_section(rag_system)
        KnowledgeBaseStats.render_stats_section(rag_system)


def render_main_content(rag_system, messages):
    should_clear = ChatInterface.render_complete_interface(rag_system, messages)

    if should_clear:
        SessionManager.clear_chat_history()


def main():
    setup_page_config()
    render_page_header()

    if not SessionManager.check_api_key():
        st.stop()

    rag_system = SessionManager.initialize_rag_system()
    messages = SessionManager.initialize_chat_history()

    render_sidebar(rag_system)
    render_main_content(rag_system, messages)


if __name__ == "__main__":
    main()
