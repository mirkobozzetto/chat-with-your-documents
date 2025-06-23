# src/ui/controllers/app_controller.py
from typing import Tuple
import streamlit as st
from src.rag_system.rag_orchestrator import RAGOrchestrator
from src.ui.adapters import StreamlitChatHistoryAdapter
from src.ui.session_manager import SessionManager
from src.ui.components import AuthComponent
from src.services.config_service import ConfigService
from src.services.message_handler import MessageHandler
from src.ui.views.main_view import MainView


class AppController:
    def __init__(self):
        self.config_service = ConfigService()
        self.message_handler = MessageHandler()
        self.main_view = MainView(self.config_service)

    def check_authentication(self) -> bool:
        auth_component = AuthComponent()
        return auth_component.protect_app()

    def initialize_systems(self) -> Tuple[RAGOrchestrator, StreamlitChatHistoryAdapter, SessionManager]:
        session_manager = SessionManager()

        if not session_manager.check_api_key():
            st.stop()

        rag_system = session_manager.initialize_rag_system()
        chat_history = StreamlitChatHistoryAdapter()

        available_docs = rag_system.get_available_documents()
        rag_system.qa_manager.sync_agents_with_documents(available_docs)

        return rag_system, chat_history, session_manager

    def handle_chat_input(self, rag_system: RAGOrchestrator, chat_history: StreamlitChatHistoryAdapter) -> None:
        if prompt := st.chat_input("Ask a question about your documents..."):
            self.message_handler.handle_user_message(prompt, rag_system, chat_history)

    def run_application(self) -> None:
        self.main_view.setup_page_config()

        if not self.check_authentication():
            return

        self.main_view.render_page_header()

        rag_system, chat_history, session_manager = self.initialize_systems()

        self.main_view.render_sidebar(rag_system, chat_history, session_manager)
        self.main_view.render_main_content(rag_system, chat_history)

        self.handle_chat_input(rag_system, chat_history)

        self.main_view.render_clear_button(chat_history)
