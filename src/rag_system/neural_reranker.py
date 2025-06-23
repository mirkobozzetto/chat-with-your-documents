# src/rag_system/neural_reranker.py
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
import logging
from dataclasses import dataclass
import re

@dataclass
class RerankedResult:
    document: Document
    original_score: float
    relevance_score: float
    final_score: float
    reasoning: str

class NeuralReranker:
    def __init__(self,
                 llm: BaseLanguageModel,
                 relevance_weight: float = 0.7,
                 original_weight: float = 0.3):
        self.llm = llm
        self.relevance_weight = relevance_weight
        self.original_weight = original_weight
        self.logger = logging.getLogger(__name__)

        self.rerank_prompt = PromptTemplate(
            template="""You are an expert at assessing document relevance for search queries.

Query: {query}

Document: {document_content}

Rate the relevance of this document to the query on a scale of 0-10, where:
- 0: Completely irrelevant
- 5: Somewhat relevant
- 10: Highly relevant and directly answers the query

Provide your rating as a single number followed by a brief explanation.

Format: SCORE: [number] REASONING: [brief explanation]""",
            input_variables=["query", "document_content"]
        )

    def rerank_documents(self,
                        query: str,
                        documents: List[Tuple[Document, float]],
                        top_k: int = 10) -> List[RerankedResult]:
        reranked_results = []

        for doc, original_score in documents:
            try:
                relevance_score, reasoning = self._assess_relevance(query, doc)

                final_score = (
                    self.relevance_weight * relevance_score +
                    self.original_weight * original_score * 10
                )

                reranked_result = RerankedResult(
                    document=doc,
                    original_score=original_score,
                    relevance_score=relevance_score,
                    final_score=final_score,
                    reasoning=reasoning
                )
                reranked_results.append(reranked_result)

            except Exception as e:
                self.logger.warning(f"Failed to rerank document: {e}")
                fallback_result = RerankedResult(
                    document=doc,
                    original_score=original_score,
                    relevance_score=5.0,
                    final_score=original_score * 10,
                    reasoning="Reranking failed, using original score"
                )
                reranked_results.append(fallback_result)

        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        return reranked_results[:top_k]

    def _assess_relevance(self, query: str, document: Document) -> Tuple[float, str]:
        prompt = self.rerank_prompt.format(
            query=query,
            document_content=document.page_content[:2000]
        )

        response = self.llm.invoke(prompt)
        response_text = response.content.strip()

        score, reasoning = self._parse_rerank_response(response_text)
        return score, reasoning

    def _parse_rerank_response(self, response: str) -> Tuple[float, str]:
        try:
            score_match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', response)
            reasoning_match = re.search(r'REASONING:\s*(.+)', response)

            if score_match:
                score = float(score_match.group(1))
                score = max(0.0, min(10.0, score))
            else:
                score = 5.0

            reasoning = reasoning_match.group(1) if reasoning_match else "No reasoning provided"

            return score, reasoning

        except Exception as e:
            self.logger.warning(f"Failed to parse rerank response: {e}")
            return 5.0, "Parsing failed"

    def batch_rerank(self,
                    query: str,
                    document_batches: List[List[Tuple[Document, float]]],
                    top_k: int = 10) -> List[RerankedResult]:
        all_reranked = []

        for batch in document_batches:
            batch_reranked = self.rerank_documents(query, batch, len(batch))
            all_reranked.extend(batch_reranked)

        all_reranked.sort(key=lambda x: x.final_score, reverse=True)
        return all_reranked[:top_k]

    def set_weights(self, relevance_weight: float, original_weight: float) -> None:
        if abs(relevance_weight + original_weight - 1.0) > 0.001:
            raise ValueError("Weights must sum to 1.0")

        self.relevance_weight = relevance_weight
        self.original_weight = original_weight

class LightweightReranker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def rerank_by_metadata(self,
                          query: str,
                          documents: List[Tuple[Document, float]],
                          top_k: int = 10) -> List[RerankedResult]:
        reranked_results = []
        query_lower = query.lower()

        for doc, original_score in documents:
            try:
                relevance_score = self._calculate_metadata_relevance(query_lower, doc)

                final_score = 0.4 * relevance_score + 0.6 * original_score * 10

                reranked_result = RerankedResult(
                    document=doc,
                    original_score=original_score,
                    relevance_score=relevance_score,
                    final_score=final_score,
                    reasoning="Metadata-based reranking"
                )
                reranked_results.append(reranked_result)

            except Exception as e:
                self.logger.warning(f"Metadata reranking failed: {e}")
                continue

        reranked_results.sort(key=lambda x: x.final_score, reverse=True)
        return reranked_results[:top_k]

    def _calculate_metadata_relevance(self, query: str, document: Document) -> float:
        score = 5.0

        title = document.metadata.get('title', '').lower()
        chapter = document.metadata.get('chapter', '').lower()
        content = document.page_content.lower()

        query_terms = query.split()

        for term in query_terms:
            if term in title:
                score += 2.0
            if term in chapter:
                score += 1.0
            if term in content:
                score += 0.5

        return min(10.0, score)
