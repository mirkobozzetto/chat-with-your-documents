import streamlit as st
import os
from rag_system_optimized import OptimizedRAGSystem as RAGSystem

# Page config
st.set_page_config(
    page_title="RAG AI Assistant",
    page_icon="🤖",
    layout="wide"
)

def main():
    st.title("🤖 RAG AI Assistant")
    st.markdown("Upload PDF documents and ask questions about their content using OpenAI embeddings.")

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY not found in environment variables!")
        st.markdown("Please set your OpenAI API key in a `.env` file:")
        st.code("OPENAI_API_KEY=your_api_key_here")
        st.stop()

    # Initialize RAG system
    if 'rag_system' not in st.session_state:
        with st.spinner("Initializing RAG system..."):
            st.session_state.rag_system = RAGSystem()

    # Sidebar for document management
    with st.sidebar:
        st.header("📚 Document Management")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload PDF document",
            type=['pdf'],
            help="Upload a PDF document to add to the knowledge base"
        )

        if uploaded_file is not None:
            if st.button("Process PDF", type="primary"):
                with st.spinner("Processing PDF..."):
                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    try:
                        st.session_state.rag_system.process_pdf(temp_path)
                        st.success(f"✅ Successfully processed {uploaded_file.name}")
                        # Force refresh of stats
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {str(e)}")
                        st.error(f"Debug info: {type(e).__name__}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        # Collection stats
        st.subheader("📊 Knowledge Base Stats")
        try:
            stats = st.session_state.rag_system.get_collection_stats()
            st.metric("Total Documents", stats["total_documents"])
        except:
            st.metric("Total Documents", "0")

    # Main chat interface
    st.header("💬 Ask Questions")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(message["sources"]):
                        st.markdown(f"**Source {i+1}:**")
                        st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.rag_system.query(prompt)

                    # Display answer
                    st.markdown(result["answer"])

                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["source_documents"]
                    })

                    # Display sources
                    with st.expander("📄 Source Documents"):
                        for i, doc in enumerate(result["source_documents"]):
                            st.markdown(f"**Source {i+1}:**")
                            st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
