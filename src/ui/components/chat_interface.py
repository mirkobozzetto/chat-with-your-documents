# ui/components/chat_interface.py
import streamlit as st
from typing import List, Dict, Any
from rag_system import OptimizedRAGSystem as RAGSystem


class ChatInterface:
    """Handles chat interface and conversation management"""

    @staticmethod
    def render_chat_header() -> None:
        """Render chat section header"""
        st.header("💬 Ask Questions")

    @staticmethod
    def render_message_history(messages: List[Dict]) -> None:
        """Render conversation history"""
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "assistant" and "sources" in message:
                    ChatInterface._render_message_sources(message["sources"])

    @staticmethod
    def _render_message_sources(sources: List) -> None:
        """Render source documents for a message"""
        with st.expander("📄 Source Documents"):
            for i, doc in enumerate(sources):
                source_file = doc.metadata.get("source_filename", "Unknown")
                st.markdown(f"**Source {i+1}** (from {source_file}):")
                content_preview = ChatInterface._get_content_preview(doc.page_content)
                st.text(content_preview)

    @staticmethod
    def _get_content_preview(content: str, max_length: int = 300) -> str:
        """Get preview of document content"""
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content

    @staticmethod
    def handle_user_input(rag_system: RAGSystem, messages: List[Dict]) -> None:
        """Handle user input and generate response"""
        if prompt := st.chat_input("Ask a question about your documents..."):
            # Add user message
            messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display response
            ChatInterface._generate_response(rag_system, prompt, messages)

    @staticmethod
    def _generate_response(rag_system: RAGSystem, prompt: str, messages: List[Dict]) -> None:
        """Generate AI response to user prompt"""
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = rag_system.ask_question(prompt, messages)

                    # Display answer
                    st.markdown(result["result"])

                    # Add to history
                    messages.append({
                        "role": "assistant",
                        "content": result["result"],
                        "sources": result["source_documents"]
                    })

                    # Display sources
                    ChatInterface._render_message_sources(result["source_documents"])

                except Exception as e:
                    ChatInterface._handle_error(e, messages)

    @staticmethod
    def _handle_error(error: Exception, messages: List[Dict]) -> None:
        """Handle and display errors"""
        error_msg = f"❌ Error: {str(error)}"
        st.error(error_msg)
        messages.append({"role": "assistant", "content": error_msg})

    @staticmethod
    def render_clear_button() -> bool:
        """Render clear chat history button"""
        return st.button("🗑️ Clear Chat History")

    @staticmethod
    def render_complete_interface(rag_system: RAGSystem, messages: List[Dict]) -> None:
        """Render complete chat interface"""
        ChatInterface.render_chat_header()
        ChatInterface.render_message_history(messages)
        ChatInterface.handle_user_input(rag_system, messages)

        if ChatInterface.render_clear_button():
            return True  # Signal to clear history
        return False
