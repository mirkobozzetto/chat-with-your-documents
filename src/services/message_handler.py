# src/services/message_handler.py
from typing import Dict, Any, List
import streamlit as st
from src.rag_system.rag_orchestrator import RAGOrchestrator
from src.ui.adapters import StreamlitChatHistoryAdapter


class MessageHandler:
    """
    Service responsible for handling user messages.
    Handles chat message processing.
    """

    def __init__(self):
        pass

    def handle_user_message(self, prompt: str, rag_system: RAGOrchestrator, chat_history: StreamlitChatHistoryAdapter) -> None:
        """Process a user message and generate response."""
        chat_history.add_message("user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = rag_system.ask_question(prompt, st.session_state.messages)

                    st.markdown(result["result"])

                    self._display_metadata_summary(result)

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

                    self._display_source_documents(result["source_documents"])

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    chat_history.add_message("assistant", error_msg)

    def _display_metadata_summary(self, result: Dict[str, Any]) -> None:
        if "metadata_summary" in result:
            metadata_summary = result["metadata_summary"]
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

    def _display_source_documents(self, source_documents: List[Any]) -> None:
        with st.expander("📄 Source Documents"):
            for i, doc in enumerate(source_documents):
                source_file = doc.metadata.get("source_filename", "Unknown")

                source_ref = f"**Source {i+1}** - {source_file}"

                page = doc.metadata.get("page")
                if page is not None:
                    source_ref += f" (Page {page})"

                chapter_num = doc.metadata.get("chapter_number")
                chapter_title = doc.metadata.get("chapter_title")
                if chapter_num:
                    chapter_info = f"Chapter {chapter_num}"
                    if chapter_title:
                        chapter_info += f": {chapter_title}"
                    source_ref += f" - {chapter_info}"

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
