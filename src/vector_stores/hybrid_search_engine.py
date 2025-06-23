# src/vector_stores/hybrid_search_engine.py
from typing import List, Dict, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_core.vectorstores import VectorStore
from dataclasses import dataclass
import logging

@dataclass
class SearchResult:
    document: Document
    dense_score: float
    sparse_score: float
    combined_score: float
    rank_position: int

class HybridSearchEngine:
    def __init__(self,
                 vector_store: VectorStore,
                 dense_weight: float = 0.6,
                 sparse_weight: float = 0.4):
        self.vector_store = vector_store
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.logger = logging.getLogger(__name__)
        self._documents_indexed = False

    def index_documents(self, documents: List[Document]) -> None:
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 20
        self._documents_indexed = True

    def hybrid_search(self,
                     query: str,
                     k: int = 10,
                     dense_k: int = 20,
                     sparse_k: int = 20) -> List[SearchResult]:
        if not self._documents_indexed:
            raise ValueError("Documents must be indexed before searching")

        dense_results = self._dense_search(query, dense_k)
        sparse_results = self._sparse_search(query, sparse_k)

        combined_results = self._combine_results(dense_results, sparse_results)
        ranked_results = self._rank_fusion(combined_results)

        return ranked_results[:k]

    def _dense_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [(doc, 1.0 / (1.0 + score)) for doc, score in results]
        except Exception as e:
            self.logger.warning(f"Dense search failed: {e}")
            return []

    def _sparse_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        try:
            if not self.bm25_retriever:
                return []

            docs = self.bm25_retriever.get_relevant_documents(query)
            scores = self.bm25_retriever.get_scores(query)

            doc_score_pairs = list(zip(docs[:k], scores[:k]))
            normalized_pairs = [(doc, self._normalize_bm25_score(score))
                              for doc, score in doc_score_pairs]

            return normalized_pairs
        except Exception as e:
            self.logger.warning(f"Sparse search failed: {e}")
            return []

    def _normalize_bm25_score(self, score: float) -> float:
        return score / (score + 1.0)

    def _combine_results(self,
                        dense_results: List[Tuple[Document, float]],
                        sparse_results: List[Tuple[Document, float]]) -> Dict[str, SearchResult]:
        combined = {}

        for doc, score in dense_results:
            doc_id = self._get_document_id(doc)
            combined[doc_id] = SearchResult(
                document=doc,
                dense_score=score,
                sparse_score=0.0,
                combined_score=0.0,
                rank_position=0
            )

        for doc, score in sparse_results:
            doc_id = self._get_document_id(doc)
            if doc_id in combined:
                combined[doc_id].sparse_score = score
            else:
                combined[doc_id] = SearchResult(
                    document=doc,
                    dense_score=0.0,
                    sparse_score=score,
                    combined_score=0.0,
                    rank_position=0
                )

        for result in combined.values():
            result.combined_score = (
                self.dense_weight * result.dense_score +
                self.sparse_weight * result.sparse_score
            )

        return combined

    def _rank_fusion(self, results: Dict[str, SearchResult]) -> List[SearchResult]:
        sorted_results = sorted(
            results.values(),
            key=lambda x: x.combined_score,
            reverse=True
        )

        for i, result in enumerate(sorted_results):
            result.rank_position = i + 1

        return sorted_results

    def _get_document_id(self, doc: Document) -> str:
        content_hash = hash(doc.page_content)
        metadata_str = str(sorted(doc.metadata.items()))
        return f"{content_hash}_{hash(metadata_str)}"

    def set_weights(self, dense_weight: float, sparse_weight: float) -> None:
        if abs(dense_weight + sparse_weight - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")

        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
