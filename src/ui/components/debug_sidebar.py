# src/ui/components/debug_sidebar.py
import streamlit as st
from typing import Dict, Any


class DebugSidebar:

    @staticmethod
    def render_retrieval_debug(rag_system) -> None:
        st.subheader("🐛 Debug RAG")

        with st.expander("Current Settings"):
            st.text(f"Retrieval K: {rag_system.qa_manager.retrieval_k}")
            st.text(f"Fetch K: {rag_system.qa_manager.retrieval_fetch_k}")
            st.text(f"Lambda: {rag_system.qa_manager.retrieval_lambda_mult}")

            stats = rag_system.get_knowledge_base_stats()
            st.text(f"Chunk Size: {stats.get('chunk_size', 'N/A')}")
            st.text(f"Strategy: {stats.get('chunk_strategy', 'N/A')}")

        test_query = st.text_input("Test Query", placeholder="Enter specific question...", key="debug_test_query")

        if test_query and st.button("🔍 Debug Retrieval", key="debug_retrieval_btn"):
            DebugSidebar._show_retrieval_details(rag_system, test_query)

    @staticmethod
    def _show_retrieval_details(rag_system, query: str) -> None:
        vector_store = rag_system.vector_store_manager.get_vector_store()
        if not vector_store:
            st.error("No vector store")
            return

        try:
            search_kwargs = {
                "k": rag_system.qa_manager.retrieval_k,
                "fetch_k": rag_system.qa_manager.retrieval_fetch_k,
                "lambda_mult": rag_system.qa_manager.retrieval_lambda_mult
            }

            document_filter = rag_system.document_selector.get_document_filter()
            if document_filter:
                search_kwargs["filter"] = document_filter
                st.info(f"🎯 Filtered to: {document_filter}")

            retriever = vector_store.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs
            )

            docs = retriever.get_relevant_documents(query)

            st.success(f"Retrieved {len(docs)} chunks")

            for i, doc in enumerate(docs):
                with st.expander(f"Chunk {i+1} - {doc.metadata.get('source_filename', 'Unknown')}"):
                    preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    st.text(preview)

                    relevance = DebugSidebar._calculate_relevance(query.lower(), doc.page_content.lower())
                    st.metric("Relevance Score", f"{relevance:.2f}")

        except Exception as e:
            st.error(f"Debug error: {str(e)}")

    @staticmethod
    def _calculate_relevance(query: str, content: str) -> float:
        query_words = set(query.split())
        content_words = set(content.split())

        if not query_words:
            return 0.0

        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)

    @staticmethod
    def render_quick_settings(rag_system) -> None:
        st.subheader("⚙️ Quick Tuning")

        col1, col2 = st.columns(2)

        with col1:
            new_k = st.selectbox("Retrieval K", [2, 3, 4, 5, 6],
                                index=[2, 3, 4, 5, 6].index(rag_system.qa_manager.retrieval_k),
                                key="debug_retrieval_k")

        with col2:
            new_lambda = st.selectbox("Lambda", [0.7, 0.8, 0.9, 0.95, 1.0],
                                    index=[0.7, 0.8, 0.9, 0.95, 1.0].index(rag_system.qa_manager.retrieval_lambda_mult),
                                    key="debug_lambda")

        if st.button("Apply & Test", key="debug_apply_btn"):
            rag_system.qa_manager.retrieval_k = new_k
            rag_system.qa_manager.retrieval_lambda_mult = new_lambda
            rag_system.qa_manager.create_qa_chain()
            st.success("✅ Settings applied!")
            st.rerun()
