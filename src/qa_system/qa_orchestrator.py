# src/qa_system/qa_orchestrator.py
from typing import Optional, List, Dict, Any
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from src.document_management import DocumentSelector
from src.agents import AgentManager
from .query_enhancer import QueryEnhancer
from .context_expander import ContextExpander
from .qa_chain_builder import QAChainBuilder
from .result_processor import ResultProcessor


class QAOrchestrator:
    """
    Orchestrates the complete QA process by coordinating all QA system components
    """

    def __init__(self, llm, vector_store_manager: BaseVectorStoreManager,
                 document_selector: DocumentSelector, retrieval_k: int,
                 retrieval_fetch_k: int, retrieval_lambda_mult: float):
        self.llm = llm
        self.vector_store_manager = vector_store_manager
        self.document_selector = document_selector
        self.retrieval_k = retrieval_k
        self.retrieval_fetch_k = retrieval_fetch_k
        self.retrieval_lambda_mult = retrieval_lambda_mult

        # Initialize QA system components
        self.query_enhancer = QueryEnhancer()
        self.context_expander = ContextExpander(vector_store_manager)
        self.chain_builder = QAChainBuilder(llm, vector_store_manager, document_selector)
        self.result_processor = ResultProcessor(enable_debug=True)

        # Agent manager for document-specific behavior
        self.agent_manager = AgentManager()

        # Main QA chain
        self.qa_chain = None

    def create_qa_chain(self) -> None:
        """Initialize the main QA chain"""
        print("🔗 Creating optimized QA chain...")

        self.qa_chain = self.chain_builder.build_standard_qa_chain(
            self.retrieval_k,
            self.retrieval_fetch_k,
            self.retrieval_lambda_mult
        )

        print("✅ QA chain ready")

    def ask_question(self, question: str, chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a question through the complete QA pipeline

        Args:
            question: User's question
            chat_history: Previous conversation context

        Returns:
            Comprehensive QA result with metadata
        """
        if not self.qa_chain:
            raise ValueError("QA chain not initialized. Process a document first.")

        print(f"\n❓ Question: {question}")

        # Get current document context
        selected_document = self.document_selector.get_selected_document()
        if self.document_selector.has_selected_document():
            print(f"📖 Querying document: {selected_document}")

            agent_config = self.agent_manager.get_agent_for_document(selected_document)
            if agent_config and agent_config.is_active:
                print(f"🤖 Using {agent_config.agent_type.value} agent")

        print("🤔 Thinking...")

        # 1. Enhance query with agent and conversation context
        enhanced_query = self._build_enhanced_query_with_agent(question, chat_history, selected_document)

        # 2. Check for chapter-specific queries
        chapter_filter = self.query_enhancer.extract_chapter_filter(question)

        if chapter_filter:
            print(f"🔍 Detected chapter query: {chapter_filter}")
            result = self._query_with_chapter_filter(enhanced_query, chapter_filter)
        else:
            result = self.qa_chain.invoke({"query": enhanced_query})

        # 3. Expand context with adjacent chunks
        if result.get("source_documents"):
            expanded_docs = self.context_expander.expand_context_with_adjacent_chunks(
                result["source_documents"]
            )
            if len(expanded_docs) > len(result["source_documents"]):
                print(f"🧠 Context expansion: {len(result['source_documents'])} → {len(expanded_docs)} chunks")
                result["source_documents"] = expanded_docs

        # 4. Process and format results
        processed_result = self.result_processor.process_qa_result(result, enhanced_query)

        # 5. Display final output
        self.result_processor.format_final_output(processed_result)

        return processed_result

    def _build_enhanced_query_with_agent(self, question: str, chat_history: Optional[List[Dict]],
                                       selected_document: Optional[str]) -> str:
        """Build enhanced query with conversation context and agent modifications"""
        # First add conversation context
        context_query = self.query_enhancer.build_context_from_history(question, chat_history)

        # Then apply agent enhancements if available
        agent_config = self.agent_manager.get_agent_for_document(selected_document)
        if agent_config and agent_config.is_active:
            return self.agent_manager.build_enhanced_prompt(
                question=context_query,
                context="{context}",
                document_name=selected_document
            )

        return context_query

    def _query_with_chapter_filter(self, query: str, chapter_filter: Dict[str, str]) -> Dict[str, Any]:
        """Execute query with chapter-specific filtering"""
        chapter_qa_chain = self.chain_builder.build_chapter_filtered_qa_chain(
            chapter_filter,
            self.retrieval_k,
            self.retrieval_fetch_k,
            self.retrieval_lambda_mult
        )

        result = chapter_qa_chain.invoke({"query": query})

        # Filter results to ensure chapter match
        return self.result_processor.filter_chapter_specific_documents(result, chapter_filter)

    def is_ready(self) -> bool:
        """Check if QA system is ready to answer questions"""
        return self.qa_chain is not None

    def update_document_selection(self) -> None:
        """Update QA chain when document selection changes"""
        if self.is_ready():
            self.create_qa_chain()

    def get_agent_manager(self) -> AgentManager:
        """Get the agent manager for external configuration"""
        return self.agent_manager

    def sync_agents_with_documents(self, available_documents: List[str]) -> None:
        """Synchronize agents with available documents"""
        self.agent_manager.sync_with_available_documents(available_documents)

    def ask_question_with_documents(self, question: str, documents: List[Any], chat_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Ask question using specific documents for contextual RAG"""
        try:
            enhanced_query = self.query_enhancer.build_context_from_history(question, chat_history)

            custom_chain = self.chain_builder.build_qa_chain_with_documents(documents)
            result = custom_chain.invoke({"query": enhanced_query})

            processed_result = self.result_processor.process_qa_result(result, enhanced_query)
            return processed_result

        except Exception as e:
            print(f"⚠️ ask_question_with_documents failed: {e}")
            return self.ask_question(question, chat_history)
