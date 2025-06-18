# app.py
import streamlit as st
from src.ui.session_manager import SessionManager
from src.ui.components import DocumentManagement, KnowledgeBaseStats, ChatInterface, AgentConfiguration, AuthComponent, DebugSidebar
from src.ui.adapters import StreamlitChatHistoryAdapter


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
        DocumentManagement.render_upload_section(rag_system)
        DocumentManagement.render_selection_section(rag_system)

        agent_manager = rag_system.qa_manager.get_agent_manager()
        AgentConfiguration.render_agent_section(rag_system, agent_manager)

        chat_history.render_conversation_sidebar()

        KnowledgeBaseStats.render_stats_section(rag_system)

        DebugSidebar.render_retrieval_debug(rag_system)
        DebugSidebar.render_quick_settings(rag_system)

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

            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(message["sources"]):
                        source_file = doc.metadata.get("source_filename", "Unknown")
                        st.markdown(f"**Source {i+1}** (from {source_file}):")
                        content_preview = doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else "")
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

                chat_history.add_message(
                    "assistant",
                    result["result"],
                    sources=[doc.metadata for doc in result["source_documents"]]
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["result"],
                    "sources": result["source_documents"]
                })

                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(result["source_documents"]):
                        source_file = doc.metadata.get("source_filename", "Unknown")
                        st.markdown(f"**Source {i+1}** (from {source_file}):")
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
