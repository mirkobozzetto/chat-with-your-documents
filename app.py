# app.py
import streamlit as st
from src.ui.session_manager import SessionManager
from src.ui.components import DocumentManagement, KnowledgeBaseStats, AgentConfiguration, AuthComponent, AdvancedControls
from src.ui.adapters import StreamlitChatHistoryAdapter


def apply_chunking_config(rag_system, config):
    rag_system.chunk_size = config["chunk_size"]
    rag_system.chunk_overlap = config["chunk_overlap"]
    rag_system.chunk_strategy = config["chunk_strategy"]
    if hasattr(rag_system, 'document_processor_manager'):
        rag_system.document_processor_manager.chunk_strategy = config["chunk_strategy"]
        rag_system.document_processor_manager.chunk_size = config["chunk_size"]
        rag_system.document_processor_manager.chunk_overlap = config["chunk_overlap"]

def apply_retrieval_config(rag_system, config):
    rag_system.qa_manager.retrieval_k = config["retrieval_k"]
    rag_system.qa_manager.retrieval_fetch_k = config["fetch_k"]
    rag_system.qa_manager.retrieval_lambda_mult = config["lambda_mult"]
    rag_system.qa_manager.create_qa_chain()

def apply_weighting_config(rag_system, config):
    if hasattr(rag_system, 'vector_store_manager'):
        vector_store = rag_system.vector_store_manager.get_vector_store()
        if hasattr(vector_store, 'search_engine'):
            search_engine = vector_store.search_engine
            search_engine.chapter_match_boost = config["chapter_match_boost"]
            search_engine.section_match_boost = config["section_match_boost"]
            search_engine.pdf_document_boost = config["pdf_document_boost"]
            search_engine.early_position_boost = config["early_position_boost"]

def apply_filter_config(rag_system, config):
    if config["document_filter"]:
        for doc in config["document_filter"]:
            rag_system.set_selected_document(doc)
    rag_system.min_chunk_length = config["min_chunk_length"]

def apply_preset_config(rag_system, preset_config):
    print(f"🎛️ Applying preset configuration: {preset_config}")

    # Apply chunking settings
    chunking_config = {
        "chunk_size": preset_config.get("chunk_size", 1500),
        "chunk_overlap": preset_config.get("chunk_overlap", 300),
        "chunk_strategy": preset_config.get("chunk_strategy", "semantic")
    }
    apply_chunking_config(rag_system, chunking_config)

    # Apply retrieval settings
    retrieval_config = {
        "retrieval_k": preset_config.get("retrieval_k", 6),
        "fetch_k": preset_config.get("fetch_k", 25),
        "lambda_mult": preset_config.get("lambda_mult", 0.8)
    }
    apply_retrieval_config(rag_system, retrieval_config)

    # Apply weighting settings
    weighting_config = {
        "chapter_match_boost": preset_config.get("chapter_match_boost", 1.8),
        "section_match_boost": preset_config.get("section_match_boost", 1.5),
        "pdf_document_boost": preset_config.get("pdf_document_boost", 1.2),
        "early_position_boost": preset_config.get("early_position_boost", 1.15)
    }
    apply_weighting_config(rag_system, weighting_config)

    print("✅ Preset configuration applied successfully")


def setup_page_config():
    st.set_page_config(
        page_title="RAG AI Assistant",
        page_icon="🤖",
        layout="wide"
    )


def check_authentication() -> bool:
    auth_component = AuthComponent()
    return auth_component.protect_app()


def render_page_header():
    st.title("🤖 RAG AI Assistant")
    st.markdown("Upload documents and ask questions about their content using OpenAI embeddings.")


def initialize_systems():
    session_manager = SessionManager()

    if not session_manager.check_api_key():
        st.stop()

    rag_system = session_manager.initialize_rag_system()
    chat_history = StreamlitChatHistoryAdapter()

    available_docs = rag_system.get_available_documents()
    rag_system.qa_manager.sync_agents_with_documents(available_docs)

    return rag_system, chat_history, session_manager


def render_sidebar(rag_system, chat_history, session_manager):
    auth_component = AuthComponent()
    auth_component.render_user_info()

    with st.sidebar:
        if st.checkbox("🔧 Advanced Settings", key="advanced_settings_toggle"):
            st.warning("⚠️ Configure before uploading documents. Changes apply to new uploads only.")
            advanced_controls = AdvancedControls()

            with st.expander("⚙️ Chunking", expanded=False):
                chunking_params = advanced_controls.render_chunking_controls(rag_system)
                if st.button("Apply Chunking Settings", key="apply_chunking"):
                    apply_chunking_config(rag_system, chunking_params)
                    st.success("✅ Chunking settings applied!")
                    st.rerun()

            with st.expander("🔍 Retrieval", expanded=False):
                retrieval_params = advanced_controls.render_retrieval_controls(rag_system)
                if st.button("Apply Retrieval Settings", key="apply_retrieval"):
                    apply_retrieval_config(rag_system, retrieval_params)
                    st.success("✅ Retrieval settings applied!")
                    st.rerun()

            with st.expander("⚖️ Scoring", expanded=False):
                weighting_params = advanced_controls.render_weighting_controls(rag_system)
                if st.button("Apply Scoring Settings", key="apply_weighting"):
                    apply_weighting_config(rag_system, weighting_params)
                    st.success("✅ Scoring settings applied!")
                    st.rerun()

            with st.expander("🎯 Filters", expanded=False):
                filter_params = advanced_controls.render_filter_controls(rag_system)
                if st.button("Apply Filter Settings", key="apply_filters"):
                    apply_filter_config(rag_system, filter_params)
                    st.success("✅ Filter settings applied!")
                    st.rerun()

            with st.expander("🎛️ Presets", expanded=False):
                selected_preset = advanced_controls.render_preset_controls()
                if selected_preset and selected_preset != "Default":
                    preset_config = advanced_controls.get_preset_config(selected_preset)
                    apply_preset_config(rag_system, preset_config)
                    st.success(f"✅ Applied {selected_preset} preset - All controls updated!")
                    st.info("📊 Check other tabs to see updated values")
                    st.rerun()

        DocumentManagement.render_upload_section(rag_system)
        DocumentManagement.render_selection_section(rag_system)

        agent_manager = rag_system.qa_manager.get_agent_manager()
        AgentConfiguration.render_agent_section(rag_system, agent_manager)

        chat_history.render_conversation_sidebar()

        KnowledgeBaseStats.render_stats_section(rag_system)

        auth_component.render_auth_status()


def render_main_content(rag_system, chat_history):
    agent_manager = rag_system.qa_manager.get_agent_manager()
    AgentConfiguration.render_agents_overview(agent_manager)

    chat_history.render_conversation_management()

    render_chat_interface(rag_system, chat_history)


def render_chat_interface(rag_system, chat_history):
    st.header("💬 Ask Questions")

    update_conversation_context(rag_system, chat_history)

    messages = st.session_state.messages

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                # Display metadata summary if available
                if "metadata_summary" in message:
                    metadata_summary = message["metadata_summary"]
                    if metadata_summary.get("chapters") or metadata_summary.get("sources"):
                        with st.expander("📊 Résumé des sources"):
                            if metadata_summary.get("total_documents"):
                                st.write(f"**Total de chunks utilisés:** {metadata_summary['total_documents']}")

                            if metadata_summary.get("chapters"):
                                chapters_list = ", ".join(metadata_summary["chapters"])
                                st.write(f"**Chapitres référencés:** {chapters_list}")

                            if metadata_summary.get("sources"):
                                st.write("**Documents sources:**")
                                for source, count in metadata_summary["sources"].items():
                                    st.write(f"  • {source}: {count} chunks")

                # Display source documents if available
                if "sources" in message:
                    with st.expander("📄 Source Documents"):
                        for i, doc in enumerate(message["sources"]):
                            # Handle both Document objects and metadata dicts
                            if hasattr(doc, 'metadata'):
                                # Document object
                                metadata = doc.metadata
                                content = doc.page_content
                            else:
                                # Metadata dict (from chat history)
                                metadata = doc
                                content = doc.get("page_content", "Contenu non disponible")

                            source_file = metadata.get("source_filename", "Unknown")

                            # Build source reference string
                            source_ref = f"**Source {i+1}** - {source_file}"

                            # Add page info if available
                            page = metadata.get("page")
                            if page is not None:
                                source_ref += f" (Page {page})"

                            # Add chapter info if available
                            chapter_num = metadata.get("chapter_number")
                            chapter_title = metadata.get("chapter_title")
                            if chapter_num:
                                chapter_info = f"Chapitre {chapter_num}"
                                if chapter_title:
                                    chapter_info += f": {chapter_title}"
                                source_ref += f" - {chapter_info}"

                            # Add section info if available
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

    if prompt := st.chat_input("Ask a question about your documents..."):
        handle_user_message(prompt, rag_system, chat_history)


def update_conversation_context(rag_system, chat_history):
    selected_doc = rag_system.selected_document
    agent_config = None

    if selected_doc:
        agent_manager = rag_system.qa_manager.get_agent_manager()
        agent_config = agent_manager.get_agent_for_document(selected_doc)

    chat_history.update_conversation_context(
        document_name=selected_doc,
        agent_type=agent_config.agent_type.value if agent_config else None
    )


def handle_user_message(prompt, rag_system, chat_history):
    chat_history.add_message("user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = rag_system.ask_question(prompt, st.session_state.messages)

                st.markdown(result["result"])

                # Display metadata summary if available
                if "metadata_summary" in result:
                    metadata_summary = result["metadata_summary"]
                    if metadata_summary.get("chapters") or metadata_summary.get("sources"):
                        with st.expander("📊 Résumé des sources"):
                            if metadata_summary.get("total_documents"):
                                st.write(f"**Total de chunks utilisés:** {metadata_summary['total_documents']}")

                            if metadata_summary.get("chapters"):
                                chapters_list = ", ".join(metadata_summary["chapters"])
                                st.write(f"**Chapitres référencés:** {chapters_list}")

                            if metadata_summary.get("sources"):
                                st.write("**Documents sources:**")
                                for source, count in metadata_summary["sources"].items():
                                    st.write(f"  • {source}: {count} chunks")

                chat_history.add_message(
                    "assistant",
                    result["result"],
                    sources=[doc.metadata for doc in result["source_documents"]],
                    metadata_summary=result.get("metadata_summary", {})
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["result"],
                    "sources": result["source_documents"],
                    "metadata_summary": result.get("metadata_summary", {})
                })

                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(result["source_documents"]):
                        source_file = doc.metadata.get("source_filename", "Unknown")

                        # Build source reference string
                        source_ref = f"**Source {i+1}** - {source_file}"

                        # Add page info if available
                        page = doc.metadata.get("page")
                        if page is not None:
                            source_ref += f" (Page {page})"

                        # Add chapter info if available
                        chapter_num = doc.metadata.get("chapter_number")
                        chapter_title = doc.metadata.get("chapter_title")
                        if chapter_num:
                            chapter_info = f"Chapitre {chapter_num}"
                            if chapter_title:
                                chapter_info += f": {chapter_title}"
                            source_ref += f" - {chapter_info}"

                        # Add section info if available
                        section_num = doc.metadata.get("section_number")
                        section_title = doc.metadata.get("section_title")
                        if section_num:
                            section_info = f"Section {section_num}"
                            if section_title:
                                section_info += f": {section_title}"
                            source_ref += f" - {section_info}"

                        st.markdown(source_ref)
                        content_preview = doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else "")
                        st.text(content_preview)

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                chat_history.add_message("assistant", error_msg)


def render_clear_button(chat_history):
    if st.button("🗑️ Clear Chat History"):
        chat_history.clear_current_conversation()
        st.rerun()


def main():
    setup_page_config()

    if not check_authentication():
        return

    render_page_header()

    rag_system, chat_history, session_manager = initialize_systems()

    render_sidebar(rag_system, chat_history, session_manager)
    render_main_content(rag_system, chat_history)

    render_clear_button(chat_history)


if __name__ == "__main__":
    main()
