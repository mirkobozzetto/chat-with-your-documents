# ui/components/document_management.py
import streamlit as st
from rag_system import OptimizedRAGSystem as RAGSystem
from src.ui.file_handler import FileHandler


class DocumentManagement:

    @staticmethod
    def render_upload_section(rag_system: RAGSystem) -> None:
        st.header("📚 Document Management")
        FileHandler.handle_file_upload(rag_system)

    @staticmethod
    def render_selection_section(rag_system: RAGSystem) -> None:
        st.subheader("📖 Document Selection")

        try:
            available_docs = rag_system.get_available_documents()

            if available_docs:
                DocumentManagement._render_document_selector(rag_system, available_docs)
                DocumentManagement._render_selection_status(rag_system)
            else:
                st.info("No documents available. Upload a document first.")

        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")

    @staticmethod
    def _render_document_selector(rag_system: RAGSystem, available_docs: list) -> None:
        current_selection = rag_system.selected_document

        selected_doc = st.selectbox(
            "Choose document to query:",
            options=["All documents"] + available_docs,
            index=0 if current_selection is None else available_docs.index(current_selection) + 1,
            help="Select which document to search in"
        )

        DocumentManagement._handle_selection_change(rag_system, selected_doc, current_selection)

    @staticmethod
    def _handle_selection_change(rag_system: RAGSystem, selected_doc: str, current_selection: str) -> None:
        if selected_doc == "All documents":
            if current_selection is not None:
                rag_system.selected_document = None
                rag_system.create_qa_chain()
                st.rerun()
        else:
            if current_selection != selected_doc:
                rag_system.set_selected_document(selected_doc)
                st.rerun()

    @staticmethod
    def _render_selection_status(rag_system: RAGSystem) -> None:
        if rag_system.selected_document:
            st.info(f"🎯 Currently querying: {rag_system.selected_document}")
        else:
            st.info("🌐 Querying all documents")

    @staticmethod
    def render_complete_section(rag_system: RAGSystem) -> None:
        with st.sidebar:
            DocumentManagement.render_upload_section(rag_system)
            DocumentManagement.render_selection_section(rag_system)
