# src/ui/views/main_view.py
from typing import Any
import streamlit as st
from src.rag_system.rag_orchestrator import RAGOrchestrator
from src.ui.adapters import StreamlitChatHistoryAdapter
from src.ui.components import DocumentManagement, KnowledgeBaseStats, AgentConfiguration, AuthComponent, AdvancedControls
from src.services.config_service import ConfigService


class MainView:
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service

    def setup_page_config(self) -> None:
        st.set_page_config(
            page_title="RAG AI Assistant",
            page_icon="🤖",
            layout="wide"
        )

    def render_page_header(self) -> None:
        st.title("🤖 RAG AI Assistant")
        st.markdown("Upload documents and ask questions about their content using OpenAI embeddings.")

    def render_sidebar(self, rag_system: RAGOrchestrator, chat_history: StreamlitChatHistoryAdapter, session_manager: Any) -> None:
        auth_component = AuthComponent()
        auth_component.render_user_info()

        with st.sidebar:
            self._render_advanced_settings(rag_system)
            self._render_document_management(rag_system)
            self._render_agent_configuration(rag_system)
            self._render_conversation_sidebar(chat_history)
            self._render_stats_section(rag_system)
            auth_component.render_auth_status()

    def render_main_content(self, rag_system: RAGOrchestrator, chat_history: StreamlitChatHistoryAdapter) -> None:
        self._display_conversation_history(chat_history)

    def _render_advanced_settings(self, rag_system: RAGOrchestrator) -> None:
        advanced_controls = AdvancedControls(self.config_service)
        advanced_controls.render_advanced_settings(rag_system)

    def _render_document_management(self, rag_system: RAGOrchestrator) -> None:
        doc_manager = DocumentManagement()
        doc_manager.render_document_section(rag_system)

    def _render_agent_configuration(self, rag_system: RAGOrchestrator) -> None:
        agent_config = AgentConfiguration()
        agent_config.render_agent_section(rag_system, rag_system.qa_manager.agent_manager)

    def _render_conversation_sidebar(self, chat_history: StreamlitChatHistoryAdapter) -> None:
        chat_history.render_conversation_sidebar()

    def _render_stats_section(self, rag_system: RAGOrchestrator) -> None:
        stats = KnowledgeBaseStats()
        stats.render_stats_section(rag_system)

    def _display_conversation_history(self, chat_history: StreamlitChatHistoryAdapter) -> None:
        if st.session_state.get("messages"):
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    if message["role"] == "assistant":
                        self._display_assistant_message_extras(message)

    def _display_assistant_message_extras(self, message: dict) -> None:
        if "metadata_summary" in message:
            metadata_summary = message["metadata_summary"]
            if metadata_summary.get("chapters") or metadata_summary.get("sources"):
                with st.expander("📊 Source Summary"):
                    if metadata_summary.get("total_documents"):
                        st.write(f"**Total chunks used:** {metadata_summary['total_documents']}")

                    if metadata_summary.get("chapters"):
                        chapters_list = ", ".join(metadata_summary["chapters"])
                        st.write(f"**Referenced chapters:** {chapters_list}")

                    if metadata_summary.get("sources"):
                        st.write("**Source documents:**")
                        for source, count in metadata_summary["sources"].items():
                            st.write(f"  • {source}: {count} chunks")

        if "sources" in message:
            with st.expander("📄 Source Documents"):
                for i, doc in enumerate(message["sources"]):
                    self._display_source_document(i, doc)

    def _display_source_document(self, index: int, doc: Any) -> None:
        if hasattr(doc, 'metadata'):
            metadata = doc.metadata
            content = doc.page_content
        else:
            metadata = doc
            content = doc.get("page_content", "Content not available")

        source_file = metadata.get("source_filename", "Unknown")

        source_ref = f"**Source {index+1}** - {source_file}"

        page = metadata.get("page")
        if page is not None:
            source_ref += f" (Page {page})"

        chapter_num = metadata.get("chapter_number")
        chapter_title = metadata.get("chapter_title")
        if chapter_num:
            chapter_info = f"Chapter {chapter_num}"
            if chapter_title:
                chapter_info += f": {chapter_title}"
            source_ref += f" - {chapter_info}"

        section_num = metadata.get("section_number")
        section_title = metadata.get("section_title")
        if section_num:
            section_info = f"Section {section_num}"
            if section_title:
                section_info += f": {section_title}"
            source_ref += f" - {section_info}"

        st.markdown(source_ref)
        content_preview = content[:300] + ("..." if len(content) > 300 else "")
        st.text(content_preview)

    def render_clear_button(self, chat_history: StreamlitChatHistoryAdapter) -> None:
        if st.button("🗑️ Clear Chat History"):
            chat_history.clear_current_conversation()
            st.rerun()
