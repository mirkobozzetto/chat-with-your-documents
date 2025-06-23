# ui/components/knowledge_base_stats.py
import streamlit as st
from src.rag_system.rag_orchestrator import RAGOrchestrator as RAGSystem


class KnowledgeBaseStats:
    @staticmethod
    def render_stats_section(rag_system: RAGSystem) -> None:
        st.subheader("📊 Knowledge Base Stats")

        try:
            stats = rag_system.get_knowledge_base_stats()

            if "status" in stats:
                KnowledgeBaseStats._render_empty_stats()
            else:
                KnowledgeBaseStats._render_populated_stats(stats, rag_system)

        except Exception as e:
            KnowledgeBaseStats._render_error_stats(e)

    @staticmethod
    def _render_empty_stats() -> None:
        st.metric("Total Documents", "0")

    @staticmethod
    def _render_populated_stats(stats: dict, rag_system: RAGSystem) -> None:
        # Main metrics
        st.metric("Total Documents", stats["total_documents"])
        st.metric("Total Chunks", stats["total_chunks"])

        # System configuration
        st.text(f"Model: {stats['chat_model']}")
        st.text(f"Embeddings: {stats['embedding_model']}")
        st.text(f"Strategy: {stats['chunk_strategy']}")

        # Available documents list
        if stats["available_documents"]:
            KnowledgeBaseStats._render_documents_list_with_actions(stats, rag_system)

    @staticmethod
    def _render_documents_list_with_actions(stats: dict, rag_system: RAGSystem) -> None:
        with st.expander("📋 Available Documents", expanded=True):
            for doc in stats["available_documents"]:
                # Get document info
                doc_info = rag_system.get_document_info(doc)

                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        if doc == stats["selected_document"]:
                            st.markdown(f"**🎯 {doc}** *(selected)*")
                        else:
                            st.markdown(f"**📄 {doc}**")

                        if doc_info:
                            st.caption(f"📦 {doc_info['chunk_count']} chunks • 📝 {doc_info['total_words']} words")
                            if doc_info['chapters']:
                                st.caption(f"📚 Chapters: {', '.join(doc_info['chapters'])}")

                    with col2:
                        if st.button("ℹ️", key=f"info_{doc}", help=f"Document info"):
                            st.session_state[f"show_info_{doc}"] = not st.session_state.get(f"show_info_{doc}", False)

                    with col3:
                        if st.button("🗑️", key=f"delete_{doc}", help=f"Delete {doc}"):
                            st.session_state[f"confirm_delete_{doc}"] = True
                            st.rerun()

                    if st.session_state.get(f"show_info_{doc}", False) and doc_info:
                        with st.expander(f"Details for {doc}", expanded=True):
                            st.json(doc_info)

                    st.divider()

    @staticmethod
    def _render_error_stats(error: Exception) -> None:
        st.metric("Total Documents", "0")
        st.text(f"Error: {str(error)}")

    @staticmethod
    def render_sidebar_section(rag_system: RAGSystem) -> None:
        with st.sidebar:
            KnowledgeBaseStats.render_stats_section(rag_system)
            KnowledgeBaseStats._handle_document_deletion(rag_system)

    @staticmethod
    def _handle_document_deletion(rag_system: RAGSystem) -> None:
        available_docs = rag_system.get_available_documents()

        for doc in available_docs:
            if st.session_state.get(f"confirm_delete_{doc}", False):
                st.warning(f"⚠️ Delete document '{doc}'?")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Confirm", key=f"confirm_yes_{doc}"):
                        with st.spinner(f"Deleting {doc}..."):
                            success = rag_system.delete_document(doc)

                        if success:
                            st.success(f"Document '{doc}' deleted successfully!")
                            del st.session_state[f"confirm_delete_{doc}"]
                            st.rerun()
                        else:
                            st.error(f"Failed to delete document '{doc}'")
                            del st.session_state[f"confirm_delete_{doc}"]

                with col2:
                    if st.button("❌ Cancel", key=f"confirm_no_{doc}"):
                        del st.session_state[f"confirm_delete_{doc}"]
                        st.rerun()
