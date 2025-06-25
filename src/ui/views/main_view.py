# src/ui/views/main_view.py
from typing import Any
import streamlit as st
from src.rag_system.rag_orchestrator import RAGOrchestrator
from src.ui.adapters import StreamlitChatHistoryAdapter
from src.ui.components import DocumentManagement, KnowledgeBaseStats, AgentConfiguration, AuthComponent, AdvancedControls
from src.ui.components.smart_preset_selector import SmartPresetSelector
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
        st.title("AI Assistant")
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
        agent_manager = rag_system.qa_manager.get_agent_manager()
        AgentConfiguration.render_agents_overview(agent_manager)

        chat_history.render_conversation_management()

        st.header("💬 Ask Questions")

        self._update_conversation_context(rag_system, chat_history)

        messages = st.session_state.messages
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "assistant":
                    self._display_assistant_message_extras(message)

    def _render_advanced_settings(self, rag_system: RAGOrchestrator) -> None:
        # Smart Presets Interface (Principal)
        if not st.session_state.get('show_expert_mode', False):
            st.subheader("🧠 Configuration Intelligente")

            smart_selector = SmartPresetSelector()

            # If a document is selected, analyze for recommendation
            current_doc = st.session_state.get('uploaded_file_path')
            if current_doc:
                selected_preset = smart_selector.render_smart_interface(current_doc)
            else:
                st.info("📄 Upload a document for automatic recommendation")
                selected_preset = smart_selector.render_preset_selection()

            # Apply the selected preset
            if selected_preset:
                preset_config = smart_selector.get_preset_config(selected_preset)
                self.config_service.apply_preset_config(rag_system, preset_config)
                st.success(f"✅ Preset {smart_selector.presets[selected_preset]['display_name']} applied!")
                st.rerun()

            # Comparison table
            with st.expander("📋 Comparaison des Presets"):
                smart_selector.render_comparison_table()

            # Expert mode button
            st.divider()
            if st.button("🔧 Expert Mode (Advanced Controls)", type="secondary"):
                st.session_state.show_expert_mode = True
                st.rerun()

        # Expert mode (Advanced Controls)
        else:
            st.subheader("🔧 Expert Mode")
            st.warning("⚠️ Configure before uploading documents. Changes apply to new uploads only.")

            # Smart presets back button
            if st.button("🧠 Back to Smart Presets", type="primary"):
                st.session_state.show_expert_mode = False
                st.rerun()

            advanced_controls = AdvancedControls()

            with st.expander("⚙️ Chunking", expanded=False):
                chunking_params = advanced_controls.render_chunking_controls(rag_system)
                if st.button("Apply Chunking Settings", key="apply_chunking"):
                    self.config_service.apply_chunking_config(rag_system, chunking_params)
                    st.success("✅ Chunking settings applied!")
                    st.rerun()

            with st.expander("🔍 Retrieval", expanded=False):
                retrieval_params = advanced_controls.render_retrieval_controls(rag_system)
                if st.button("Apply Retrieval Settings", key="apply_retrieval"):
                    self.config_service.apply_retrieval_config(rag_system, retrieval_params)
                    st.success("✅ Retrieval settings applied!")
                    st.rerun()

            with st.expander("⚖️ Scoring", expanded=False):
                weighting_params = advanced_controls.render_weighting_controls(rag_system)
                if st.button("Apply Scoring Settings", key="apply_weighting"):
                    self.config_service.apply_weighting_config(rag_system, weighting_params)
                    st.success("✅ Scoring settings applied!")
                    st.rerun()

            with st.expander("🎯 Filters", expanded=False):
                filter_params = advanced_controls.render_filter_controls(rag_system)
                if st.button("Apply Filter Settings", key="apply_filters"):
                    self.config_service.apply_filter_config(rag_system, filter_params)
                    st.success("✅ Filter settings applied!")
                    st.rerun()

            with st.expander("🎛️ Presets Legacy", expanded=False):
                selected_preset = advanced_controls.render_preset_controls()
                if selected_preset and selected_preset != "Default":
                    preset_config = advanced_controls.get_preset_config(selected_preset)
                    self.config_service.apply_preset_config(rag_system, preset_config)
                    st.success(f"✅ Applied {selected_preset} preset - All controls updated!")
                    st.info("📊 Check other tabs to see updated values")
                    st.rerun()

    def _render_document_management(self, rag_system: RAGOrchestrator) -> None:
        DocumentManagement.render_upload_section(rag_system)
        DocumentManagement.render_selection_section(rag_system)

    def _render_agent_configuration(self, rag_system: RAGOrchestrator) -> None:
        agent_manager = rag_system.qa_manager.get_agent_manager()
        AgentConfiguration.render_agent_section(rag_system, agent_manager)

    def _render_conversation_sidebar(self, chat_history: StreamlitChatHistoryAdapter) -> None:
        chat_history.render_conversation_sidebar()

    def _render_stats_section(self, rag_system: RAGOrchestrator) -> None:
        KnowledgeBaseStats.render_stats_section(rag_system)

    def _update_conversation_context(self, rag_system: RAGOrchestrator, chat_history: StreamlitChatHistoryAdapter) -> None:
        selected_doc = rag_system.selected_document
        agent_config = None

        if selected_doc:
            agent_manager = rag_system.qa_manager.get_agent_manager()
            agent_config = agent_manager.get_agent_for_document(selected_doc)

        chat_history.update_conversation_context(
            document_name=selected_doc,
            agent_type=agent_config.agent_type.value if agent_config else None
        )

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
