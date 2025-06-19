# src/qa_system/qa_manager.py
from typing import Optional, List, Dict, Any
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from src.document_management import DocumentSelector
from .qa_orchestrator import QAOrchestrator
from src.agents import AgentManager


class QAManager:

    def __init__(self, llm, vector_store_manager: BaseVectorStoreManager,
                 document_selector: DocumentSelector, retrieval_k: int,
                 retrieval_fetch_k: int, retrieval_lambda_mult: float):
        self.qa_orchestrator = QAOrchestrator(
            llm=llm,
            vector_store_manager=vector_store_manager,
            document_selector=document_selector,
            retrieval_k=retrieval_k,
            retrieval_fetch_k=retrieval_fetch_k,
            retrieval_lambda_mult=retrieval_lambda_mult
        )

    def create_qa_chain(self) -> None:
        self.qa_orchestrator.create_qa_chain()

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return self.qa_orchestrator.ask_question(question, chat_history)

    def is_ready(self) -> bool:
        return self.qa_orchestrator.is_ready()

    def update_document_selection(self) -> None:
        self.qa_orchestrator.update_document_selection()

    def get_agent_manager(self) -> AgentManager:
        return self.qa_orchestrator.get_agent_manager()

    def sync_agents_with_documents(self, available_documents: List[str]) -> None:
        self.qa_orchestrator.sync_agents_with_documents(available_documents)
