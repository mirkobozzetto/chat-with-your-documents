# ui/file_handler.py
import os
import streamlit as st
from typing import Optional
from rag_system import OptimizedRAGSystem as RAGSystem


class FileHandler:

    @staticmethod
    def save_uploaded_file(uploaded_file) -> str:
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return temp_path

    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def process_document(rag_system: RAGSystem, file_path: str, filename: str) -> bool:
        try:
            rag_system.process_pdf(file_path)
            st.success(f"✅ Successfully processed {filename}")
            return True
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
            st.error(f"Debug info: {type(e).__name__}")
            return False

    @staticmethod
    def handle_file_upload(rag_system: RAGSystem) -> bool:
        uploaded_file = st.file_uploader(
            "Upload document",
            type=['pdf', 'docx', 'txt', 'md'],
            help="Upload a document to add to the knowledge base"
        )

        if uploaded_file is not None:
            if st.button("Process Document", type="primary"):
                with st.spinner("Processing document..."):
                    temp_path = FileHandler.save_uploaded_file(uploaded_file)

                    try:
                        success = FileHandler.process_document(
                            rag_system, temp_path, uploaded_file.name
                        )
                        if success:
                            st.rerun()
                        return success
                    finally:
                        FileHandler.cleanup_temp_file(temp_path)

        return False
