# src/rag_system/rank_fusion.py
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

@dataclass
class RankedResult:
    document: Document
    score: float
    rank: int
    method: str

class RankFusionStrategy(ABC):
    @abstractmethod
    def fuse_rankings(self,
                     rankings: Dict[str, List[RankedResult]]) -> List[RankedResult]:
        pass

class ReciprocalRankFusion(RankFusionStrategy):
    def __init__(self, k: int = 60):
        self.k = k

    def fuse_rankings(self,
                     rankings: Dict[str, List[RankedResult]]) -> List[RankedResult]:
        doc_scores = {}

        for method, results in rankings.items():
            for result in results:
                doc_id = self._get_document_id(result.document)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'document': result.document,
                        'rrf_score': 0.0,
                        'method_scores': {}
                    }

                rrf_score = 1.0 / (self.k + result.rank)
                doc_scores[doc_id]['rrf_score'] += rrf_score
                doc_scores[doc_id]['method_scores'][method] = result.score

        fused_results = []
        for doc_id, data in doc_scores.items():
            fused_result = RankedResult(
                document=data['document'],
                score=data['rrf_score'],
                rank=0,
                method='rrf_fusion'
            )
            fused_results.append(fused_result)

        fused_results.sort(key=lambda x: x.score, reverse=True)

        for i, result in enumerate(fused_results):
            result.rank = i + 1

        return fused_results

    def _get_document_id(self, doc: Document) -> str:
        content_hash = hash(doc.page_content)
        metadata_str = str(sorted(doc.metadata.items()))
        return f"{content_hash}_{hash(metadata_str)}"

class WeightedScoreFusion(RankFusionStrategy):
    def __init__(self, method_weights: Dict[str, float]):
        self.method_weights = method_weights
        total_weight = sum(method_weights.values())
        self.method_weights = {k: v/total_weight for k, v in method_weights.items()}

    def fuse_rankings(self,
                     rankings: Dict[str, List[RankedResult]]) -> List[RankedResult]:
        doc_scores = {}

        for method, results in rankings.items():
            weight = self.method_weights.get(method, 0.0)

            for result in results:
                doc_id = self._get_document_id(result.document)

                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'document': result.document,
                        'weighted_score': 0.0,
                        'method_scores': {}
                    }

                weighted_score = weight * result.score
                doc_scores[doc_id]['weighted_score'] += weighted_score
                doc_scores[doc_id]['method_scores'][method] = result.score

        fused_results = []
        for doc_id, data in doc_scores.items():
            fused_result = RankedResult(
                document=data['document'],
                score=data['weighted_score'],
                rank=0,
                method='weighted_fusion'
            )
            fused_results.append(fused_result)

        fused_results.sort(key=lambda x: x.score, reverse=True)

        for i, result in enumerate(fused_results):
            result.rank = i + 1

        return fused_results

    def _get_document_id(self, doc: Document) -> str:
        content_hash = hash(doc.page_content)
        metadata_str = str(sorted(doc.metadata.items()))
        return f"{content_hash}_{hash(metadata_str)}"

class RankFusionEngine:
    def __init__(self, strategy: RankFusionStrategy):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

    def fuse_multiple_rankings(self,
                              rankings: Dict[str, List[Tuple[Document, float]]]) -> List[Document]:
        try:
            ranked_results = {}

            for method, doc_score_pairs in rankings.items():
                ranked_list = []
                for i, (doc, score) in enumerate(doc_score_pairs):
                    ranked_result = RankedResult(
                        document=doc,
                        score=score,
                        rank=i + 1,
                        method=method
                    )
                    ranked_list.append(ranked_result)
                ranked_results[method] = ranked_list

            fused_results = self.strategy.fuse_rankings(ranked_results)

            return [result.document for result in fused_results]

        except Exception as e:
            self.logger.error(f"Rank fusion failed: {e}")
            fallback_docs = []
            for doc_score_pairs in rankings.values():
                fallback_docs.extend([doc for doc, _ in doc_score_pairs])
            return fallback_docs[:10]

    def set_strategy(self, strategy: RankFusionStrategy) -> None:
        self.strategy = strategy
