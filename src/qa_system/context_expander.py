# src/qa_system/context_expander.py
from typing import List, Dict, Any
from langchain.schema import Document
from src.vector_stores.base_vector_store import BaseVectorStoreManager


class ContextExpander:
    """
    Expand context by retrieving adjacent chunks for better continuity
    """

    def __init__(self, vector_store_manager: BaseVectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.max_expanded_docs = 12
        self.adjacent_chunk_range = 2
        self.max_adjacent_chunks = 3

    def expand_context_with_adjacent_chunks(self, source_documents: List[Document]) -> List[Document]:
        """
        Add adjacent chunks to improve context continuity

        Args:
            source_documents: Original retrieved documents

        Returns:
            List of documents with adjacent chunks added
        """
        if not source_documents:
            return source_documents

        # Group documents by filename
        docs_by_file = self._group_documents_by_file(source_documents)

        expanded_docs = []

        for filename, docs in docs_by_file.items():
            # Sort by chunk index for each file
            docs_with_index = [(doc, doc.metadata.get('chunk_index', 0)) for doc in docs]
            docs_with_index.sort(key=lambda x: x[1])

            expanded_file_docs = []

            # Add original docs and their adjacent chunks
            for doc, chunk_index in docs_with_index:
                expanded_file_docs.append(doc)
                adjacent_chunks = self._get_adjacent_chunks(filename, chunk_index)
                expanded_file_docs.extend(adjacent_chunks)

            # Remove duplicates based on content
            unique_docs = self._remove_duplicate_documents(expanded_file_docs)
            expanded_docs.extend(unique_docs)

        return expanded_docs[:self.max_expanded_docs]

    def _group_documents_by_file(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """Group documents by their source filename"""
        docs_by_file = {}

        for doc in documents:
            filename = doc.metadata.get('source_filename', 'unknown')
            if filename not in docs_by_file:
                docs_by_file[filename] = []
            docs_by_file[filename].append(doc)

        return docs_by_file

    def _get_adjacent_chunks(self, filename: str, target_index: int) -> List[Document]:
        """
        Retrieve chunks adjacent to a given index for context continuity

        Args:
            filename: Source filename to search in
            target_index: The chunk index to find adjacent chunks for

        Returns:
            List of adjacent documents
        """
        try:
            vector_store = self.vector_store_manager.get_vector_store()
            if not vector_store:
                return []

            search_kwargs = {
                "k": 6,
                "fetch_k": 15,
                "filter": {
                    "source_filename": filename
                }
            }

            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            )

            # Use a generic query to get documents from the same file
            nearby_docs = retriever.get_relevant_documents("the and of")

            adjacent = []
            for doc in nearby_docs:
                doc_index = doc.metadata.get('chunk_index', 0)
                # Check if chunk is adjacent (within range) but not the same
                if (abs(doc_index - target_index) <= self.adjacent_chunk_range and
                    doc_index != target_index):
                    adjacent.append(doc)

            return adjacent[:self.max_adjacent_chunks]

        except Exception as e:
            print(f"⚠️ Error retrieving adjacent chunks: {e}")
            return []

    def _remove_duplicate_documents(self, documents: List[Document]) -> List[Document]:
        """
        Remove duplicate documents based on content hash

        Args:
            documents: List of documents that may contain duplicates

        Returns:
            List of unique documents
        """
        seen_content = set()
        unique_docs = []

        for doc in documents:
            # Use first 100 characters as content hash for deduplication
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)

        return unique_docs
