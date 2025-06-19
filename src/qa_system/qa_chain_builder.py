# src/qa_system/qa_chain_builder.py
from typing import Optional, Dict, Any
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from src.document_management import DocumentSelector


class QAChainBuilder:
    """
    Build and configure QA chains with appropriate retrievers and prompts
    """

    def __init__(self, llm, vector_store_manager: BaseVectorStoreManager,
                 document_selector: DocumentSelector):
        self.llm = llm
        self.vector_store_manager = vector_store_manager
        self.document_selector = document_selector

        # Default prompt template
        self.default_prompt_template = """Use the following context to answer the question accurately and comprehensively.
Respond in the same language as the question.

Context:
{context}

Question: {question}

Instructions:
- Analyze the full context to understand relationships between different sections
- Cite specific passages when they support your answer
- If the context lacks sufficient information, state this clearly
- Provide thorough explanations for complex topics
- Maintain accuracy to the source material

Answer:"""

    def build_standard_qa_chain(self, retrieval_k: int, retrieval_fetch_k: int,
                              retrieval_lambda_mult: float) -> RetrievalQA:
        """
        Build a standard QA chain with MMR retrieval

        Args:
            retrieval_k: Number of documents to retrieve
            retrieval_fetch_k: Number of documents to fetch before MMR filtering
            retrieval_lambda_mult: Lambda multiplier for MMR diversity

        Returns:
            Configured RetrievalQA chain
        """
        vector_store = self.vector_store_manager.get_vector_store()
        if not vector_store:
            raise ValueError("Vector store not available")

        search_kwargs = {
            "k": retrieval_k,
            "fetch_k": retrieval_fetch_k,
            "lambda_mult": retrieval_lambda_mult
        }

        # Apply document filtering if a document is selected
        document_filter = self.document_selector.get_document_filter()
        if document_filter:
            search_kwargs["filter"] = document_filter
            selected_doc = self.document_selector.get_selected_document()
            print(f"🎯 Filtering results to document: {selected_doc}")

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        prompt = PromptTemplate(
            template=self.default_prompt_template,
            input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False,
            chain_type_kwargs={"prompt": prompt}
        )

        return qa_chain

    def build_chapter_filtered_qa_chain(self, chapter_filter: Dict[str, str],
                                      retrieval_k: int, retrieval_fetch_k: int,
                                      retrieval_lambda_mult: float) -> RetrievalQA:
        """
        Build a QA chain with chapter-specific filtering

        Args:
            chapter_filter: Dictionary with chapter/section filters
            retrieval_k: Number of documents to retrieve
            retrieval_fetch_k: Number of documents to fetch before MMR filtering
            retrieval_lambda_mult: Lambda multiplier for MMR diversity

        Returns:
            Configured RetrievalQA chain with chapter filtering
        """
        vector_store = self.vector_store_manager.get_vector_store()
        if not vector_store:
            raise ValueError("Vector store not available")

        # Build comprehensive metadata filter
        metadata_filter = {}

        # Add document filter if document is selected
        document_filter = self.document_selector.get_document_filter()
        if document_filter:
            metadata_filter.update(document_filter)

        # Add chapter-specific filters
        metadata_filter.update(chapter_filter)

        search_kwargs = {
            "k": retrieval_k * 2,  # Get more results for better chapter matching
            "fetch_k": retrieval_fetch_k * 2,
            "lambda_mult": retrieval_lambda_mult,
            "filter": metadata_filter
        }

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        # Use default prompt for chapter queries
        prompt = PromptTemplate(
            template=self.default_prompt_template,
            input_variables=["context", "question"]
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=False,
            chain_type_kwargs={"prompt": prompt}
        )

        return qa_chain

    def set_custom_prompt_template(self, template: str) -> None:
        """Set a custom prompt template"""
        self.default_prompt_template = template
