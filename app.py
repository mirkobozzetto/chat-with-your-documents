# app.py

import streamlit as st
import os
from rag_system import OptimizedRAGSystem as RAGSystem

st.set_page_config(
    page_title="RAG AI Assistant",
    page_icon="🤖",
    layout="wide"
)

def main():
    st.title("🤖 RAG AI Assistant")
    st.markdown("Upload documents and ask questions about their content using OpenAI embeddings.")

    if not os.getenv("OPENAI_API_KEY"):
        st.error("❌ OPENAI_API_KEY not found in environment variables!")
        st.markdown("Please set your OpenAI API key in a `.env` file:")
        st.code("OPENAI_API_KEY=your_api_key_here")
        st.stop()

    if 'rag_system' not in st.session_state:
        with st.spinner("Initializing RAG system..."):
            st.session_state.rag_system = RAGSystem()

    with st.sidebar:
        st.header("📚 Document Management")

        uploaded_file = st.file_uploader(
            "Upload document",
            type=['pdf', 'docx', 'txt', 'md'],
            help="Upload a document to add to the knowledge base"
        )

        if uploaded_file is not None:
            if st.button("Process Document", type="primary"):
                with st.spinner("Processing document..."):
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    try:
                        st.session_state.rag_system.process_pdf(temp_path)
                        st.success(f"✅ Successfully processed {uploaded_file.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error processing document: {str(e)}")
                        st.error(f"Debug info: {type(e).__name__}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        st.subheader("📖 Document Selection")
        try:
            available_docs = st.session_state.rag_system.get_available_documents()
            if available_docs:
                current_selection = st.session_state.rag_system.selected_document

                selected_doc = st.selectbox(
                    "Choose document to query:",
                    options=["All documents"] + available_docs,
                    index=0 if current_selection is None else available_docs.index(current_selection) + 1,
                    help="Select which document to search in"
                )

                if selected_doc == "All documents":
                    if current_selection is not None:
                        st.session_state.rag_system.selected_document = None
                        st.session_state.rag_system.create_qa_chain()
                        st.rerun()
                else:
                    if current_selection != selected_doc:
                        st.session_state.rag_system.set_selected_document(selected_doc)
                        st.rerun()

                if st.session_state.rag_system.selected_document:
                    st.info(f"🎯 Currently querying: {st.session_state.rag_system.selected_document}")
                else:
                    st.info("🌐 Querying all documents")
            else:
                st.info("No documents available. Upload a document first.")
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")

        st.subheader("📊 Knowledge Base Stats")
        try:
            stats = st.session_state.rag_system.get_knowledge_base_stats()
            if "status" in stats:
                st.metric("Total Documents", "0")
            else:
                st.metric("Total Documents", stats["total_documents"])
                st.metric("Total Chunks", stats["total_chunks"])
                st.text(f"Model: {stats['chat_model']}")
                st.text(f"Embeddings: {stats['embedding_model']}")
                st.text(f"Strategy: {stats['chunk_strategy']}")

                if stats["available_documents"]:
                    with st.expander("📋 Available Documents"):
                        for doc in stats["available_documents"]:
                            if doc == stats["selected_document"]:
                                st.text(f"🎯 {doc} (selected)")
                            else:
                                st.text(f"📄 {doc}")
        except Exception as e:
            st.metric("Total Documents", "0")
            st.text(f"Error: {str(e)}")

    st.header("💬 Ask Questions")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📄 Source Documents"):
                    for i, doc in enumerate(message["sources"]):
                        source_file = doc.metadata.get("source_filename", "Unknown")
                        st.markdown(f"**Source {i+1}** (from {source_file}):")
                        st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.rag_system.ask_question(prompt, st.session_state.messages)

                    st.markdown(result["result"])

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["result"],
                        "sources": result["source_documents"]
                    })

                    with st.expander("📄 Source Documents"):
                        for i, doc in enumerate(result["source_documents"]):
                            source_file = doc.metadata.get("source_filename", "Unknown")
                            st.markdown(f"**Source {i+1}** (from {source_file}):")
                            st.text(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
