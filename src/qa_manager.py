# src/qa_manager.py
from typing import Optional, List, Dict, Any
from langchain.chains import RetrievalQA
from src.vector_store_manager import VectorStoreManager
from src.document_selector import DocumentSelector


class QAManager:

    def __init__(self, llm, vector_store_manager: VectorStoreManager,
                 document_selector: DocumentSelector, retrieval_k: int,
                 retrieval_fetch_k: int, retrieval_lambda_mult: float):
        self.llm = llm
        self.vector_store_manager = vector_store_manager
        self.document_selector = document_selector
        self.retrieval_k = retrieval_k
        self.retrieval_fetch_k = retrieval_fetch_k
        self.retrieval_lambda_mult = retrieval_lambda_mult
        self.qa_chain = None

    def create_qa_chain(self) -> None:
        print("🔗 Creating optimized QA chain...")

        vector_store = self.vector_store_manager.get_vector_store()
        if not vector_store:
            raise ValueError("Vector store not available")

        search_kwargs = {
            "k": self.retrieval_k,
            "fetch_k": self.retrieval_fetch_k,
            "lambda_mult": self.retrieval_lambda_mult
        }

        document_filter = self.document_selector.get_document_filter()
        if document_filter:
            search_kwargs["filter"] = document_filter
            print(f"🎯 Filtering results to document: {self.document_selector.get_selected_document()}")

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False
        )

        print("✅ QA chain ready")

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Process a document first.")

        print(f"\n❓ Question: {question}")
        if self.document_selector.has_selected_document():
            print(f"📖 Querying document: {self.document_selector.get_selected_document()}")
        print("🤔 Thinking...")

        enhanced_query = self._build_enhanced_query(question, chat_history)

        result = self.qa_chain.invoke({"query": enhanced_query})

        print(f"\n💡 Answer: {result['result']}")
        print(f"\n📚 Sources used: {len(result['source_documents'])} chunks")

        return result

    def _build_enhanced_query(self, question: str, chat_history: Optional[List[Dict]]) -> str:
        if chat_history and len(chat_history) > 0:
            context_messages = []
            for msg in chat_history[-6:]:
                role = "Human" if msg["role"] == "user" else "Assistant"
                context_messages.append(f"{role}: {msg['content']}")

            conversation_context = "\n".join(context_messages)
            enhanced_query = f"""Previous conversation:
{conversation_context}

Current question: {question}

Please answer the current question considering the conversation context above."""

            print("🧠 Using conversation context...")
            return enhanced_query
        else:
            return question

    def is_ready(self) -> bool:
        return self.qa_chain is not None

    def update_document_selection(self) -> None:
        if self.is_ready():
            self.create_qa_chain()
