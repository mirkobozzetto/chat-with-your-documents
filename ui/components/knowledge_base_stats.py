# ui/components/knowledge_base_stats.py
import streamlit as st
from rag_system import OptimizedRAGSystem as RAGSystem


class KnowledgeBaseStats:

    @staticmethod
    def render_stats_section(rag_system: RAGSystem) -> None:
        st.subheader("📊 Knowledge Base Stats")

        try:
            stats = rag_system.get_knowledge_base_stats()

            if "status" in stats:
                KnowledgeBaseStats._render_empty_stats()
            else:
                KnowledgeBaseStats._render_populated_stats(stats)

        except Exception as e:
            KnowledgeBaseStats._render_error_stats(e)

    @staticmethod
    def _render_empty_stats() -> None:
        st.metric("Total Documents", "0")

    @staticmethod
    def _render_populated_stats(stats: dict) -> None:
        # Main metrics
        st.metric("Total Documents", stats["total_documents"])
        st.metric("Total Chunks", stats["total_chunks"])

        # System configuration
        st.text(f"Model: {stats['chat_model']}")
        st.text(f"Embeddings: {stats['embedding_model']}")
        st.text(f"Strategy: {stats['chunk_strategy']}")

        # Available documents list
        if stats["available_documents"]:
            KnowledgeBaseStats._render_documents_list(stats)

    @staticmethod
    def _render_documents_list(stats: dict) -> None:
        with st.expander("📋 Available Documents"):
            for doc in stats["available_documents"]:
                if doc == stats["selected_document"]:
                    st.text(f"🎯 {doc} (selected)")
                else:
                    st.text(f"📄 {doc}")

    @staticmethod
    def _render_error_stats(error: Exception) -> None:
        st.metric("Total Documents", "0")
        st.text(f"Error: {str(error)}")

    @staticmethod
    def render_sidebar_section(rag_system: RAGSystem) -> None:
        with st.sidebar:
            KnowledgeBaseStats.render_stats_section(rag_system)
