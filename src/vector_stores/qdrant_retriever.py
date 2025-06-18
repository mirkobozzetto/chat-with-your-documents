# src/vector_stores/qdrant_retriever.py
from typing import List, Dict, Any, Optional
from langchain.schema import BaseRetriever, Document
from pydantic import Field
from .qdrant_search_engine import QdrantSearchEngine


class QdrantRetriever(BaseRetriever):
    """Custom retriever for Qdrant with weighted scoring and MMR filtering"""
    
    # Declare Pydantic fields to avoid validation errors
    client: Any = Field(default=None, exclude=True)
    collection_name: str = Field(default="", exclude=True) 
    embeddings: Any = Field(default=None, exclude=True)
    search_engine: QdrantSearchEngine = Field(default_factory=QdrantSearchEngine, exclude=True)

    def __init__(self, client, collection_name: str, embeddings):
        super().__init__()
        self.client = client
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.search_engine = QdrantSearchEngine()

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Get relevant documents using weighted scoring"""
        try:
            query_vector = self.embeddings.embed_query(query)

            # Extract search parameters
            search_kwargs = kwargs.get('search_kwargs', {})
            limit = search_kwargs.get('k', kwargs.get('k', 4))
            fetch_k = search_kwargs.get('fetch_k', limit * 3)
            search_filter = search_kwargs.get('filter', None)

            print(f"🔍 Qdrant search - limit: {limit}, fetch_k: {fetch_k}, filter: {search_filter}")

            # Build Qdrant filter
            qdrant_filter = self._build_qdrant_filter(search_filter)

            # Execute search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=fetch_k,
                with_payload=True,
                filter=qdrant_filter
            )

            # Apply weighted scoring to results
            weighted_results = self.search_engine.apply_weighted_scoring(results, query, search_kwargs)

            # Convert to Document objects
            documents = self._convert_to_documents(weighted_results)

            # Apply MMR filtering if we have more results than needed
            if len(documents) > limit:
                documents = self._apply_mmr_filtering(documents, query, limit, search_kwargs.get('lambda_mult', 0.5))

            print(f"📊 Retrieved {len(documents)} weighted and filtered documents")
            return documents[:limit]

        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return []

    def _build_qdrant_filter(self, search_filter: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Build Qdrant filter from search parameters"""
        if not search_filter:
            return None

        must_conditions = []
        for key, value in search_filter.items():
            must_conditions.append({
                "key": f"metadata.{key}",
                "match": {"value": value}
            })

        if must_conditions:
            qdrant_filter = {"must": must_conditions}
            print(f"🎯 Applied filter: {qdrant_filter}")
            return qdrant_filter

        return None

    def _convert_to_documents(self, weighted_results: List[Any]) -> List[Document]:
        """Convert search results to Document objects"""
        documents = []
        for result in weighted_results:
            if result.payload:
                doc = Document(
                    page_content=result.payload.get('page_content', ''),
                    metadata=result.payload.get('metadata', {})
                )
                # Store the weighted score in metadata for debugging
                doc.metadata['_weighted_score'] = getattr(result, 'weighted_score', result.score)
                documents.append(doc)
        return documents

    def _apply_mmr_filtering(self, documents: List[Document], query: str, k: int, lambda_mult: float) -> List[Document]:
        """Apply Maximum Marginal Relevance filtering"""
        if len(documents) <= k:
            return documents

        # Simple MMR approximation - select diverse documents
        selected = [documents[0]]  # Start with most relevant
        remaining = documents[1:]

        while len(selected) < k and remaining:
            best_idx = 0
            best_score = -1

            for i, doc in enumerate(remaining):
                # Calculate diversity score based on metadata differences
                diversity_score = self._calculate_diversity_score(doc, selected)

                # Combine relevance (position in list) with diversity
                relevance_score = 1.0 / (i + 1)
                combined_score = lambda_mult * relevance_score + (1 - lambda_mult) * diversity_score

                if combined_score > best_score:
                    best_score = combined_score
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _calculate_diversity_score(self, doc: Document, selected: List[Document]) -> float:
        """Calculate diversity score for MMR filtering"""
        diversity_score = 0

        for selected_doc in selected:
            # Chapter diversity
            if doc.metadata.get('chapter_number') != selected_doc.metadata.get('chapter_number'):
                diversity_score += 0.3

            # Section diversity
            if doc.metadata.get('section_number') != selected_doc.metadata.get('section_number'):
                diversity_score += 0.2

            # Content length diversity
            if abs(len(doc.page_content) - len(selected_doc.page_content)) > 100:
                diversity_score += 0.1

        return diversity_score
