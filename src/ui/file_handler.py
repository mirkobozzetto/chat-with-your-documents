# src/ui/file_handler.py
import os
import time
import streamlit as st
from typing import Optional
from src.rag_system.rag_orchestrator import RAGOrchestrator as RAGSystem


class FileHandler:

    @staticmethod
    def save_uploaded_file(uploaded_file) -> str:
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Store file path in session for smart preset analysis
        st.session_state.uploaded_file_path = temp_path
        st.session_state.uploaded_file_name = uploaded_file.name
        
        return temp_path

    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)

    @staticmethod
    def process_document(rag_system: RAGSystem, file_path: str, filename: str) -> bool:
        file_size_mb = FileHandler.get_file_size_mb(file_path)
        estimated_time = rag_system.doc_processor_manager.get_document_processor().estimate_processing_time(file_size_mb)

        st.info(f"📊 File size: {file_size_mb:.1f} MB | Estimated time: {estimated_time}")

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(progress: float, message: str):
            progress_bar.progress(progress)
            status_text.text(f"⚡ {message}")

        try:
            start_time = time.time()

            rag_system.process_pdf(file_path, progress_callback=update_progress)

            processing_time = time.time() - start_time

            progress_bar.progress(1.0)
            status_text.text(f"✅ Completed in {processing_time:.1f}s")

            st.success(f"✅ Successfully processed {filename} in {processing_time:.1f} seconds!")

            with st.expander("📈 Performance Metrics"):
                st.metric("Processing Time", f"{processing_time:.1f}s")
                st.metric("File Size", f"{file_size_mb:.1f} MB")

            return True

        except Exception as e:
            progress_bar.progress(0)
            status_text.text("❌ Processing failed")
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
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.info(f"📄 **{uploaded_file.name}** ({file_size_mb:.1f} MB)")

            with col2:
                if file_size_mb > 50:
                    st.warning("⚠️ Large file")
                elif file_size_mb > 10:
                    st.info("📊 Medium file")
                else:
                    st.success("⚡ Small file")

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
