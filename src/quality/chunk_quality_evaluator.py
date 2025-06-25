# src/quality/chunk_quality_evaluator.py
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.schema import Document
import numpy as np


@dataclass
class ChunkQualityScore:
    semantic_coherence: float
    size_consistency: float
    overlap_quality: float
    information_density: float
    overall_score: float


class ChunkQualityEvaluator:

    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model
        self.embedding_model = None
        self.min_chunk_size = 100
        self.max_chunk_size = 2000
        self.optimal_chunk_size = 1000

    def evaluate_chunks(self, chunks: List[Document]) -> ChunkQualityScore:
        if not chunks:
            return ChunkQualityScore(0.0, 0.0, 0.0, 0.0, 0.0)

        semantic_score = self._calculate_semantic_coherence(chunks)
        size_score = self._calculate_size_consistency(chunks)
        overlap_score = self._calculate_overlap_quality(chunks)
        density_score = self._calculate_information_density(chunks)

        overall_score = (
            semantic_score * 0.4 +
            size_score * 0.2 +
            overlap_score * 0.2 +
            density_score * 0.2
        )

        return ChunkQualityScore(
            semantic_coherence=semantic_score,
            size_consistency=size_score,
            overlap_quality=overlap_score,
            information_density=density_score,
            overall_score=overall_score
        )

    def _calculate_semantic_coherence(self, chunks: List[Document]) -> float:
        if len(chunks) < 2:
            return 1.0

        try:
            if self.embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(self.embedding_model_name)

            chunk_texts = [chunk.page_content for chunk in chunks]
            embeddings = self.embedding_model.encode(chunk_texts)

            from sklearn.metrics.pairwise import cosine_similarity
            coherence_scores = []
            for i in range(len(embeddings) - 1):
                similarity = cosine_similarity(
                    embeddings[i].reshape(1, -1),
                    embeddings[i + 1].reshape(1, -1)
                )[0][0]
                coherence_scores.append(similarity)

            return float(np.mean(coherence_scores))
        except Exception as e:
            print(f"⚠️ Semantic coherence calculation failed: {e}")
            return 0.7

    def _calculate_size_consistency(self, chunks: List[Document]) -> float:
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]

        if not chunk_sizes:
            return 0.0

        mean_size = np.mean(chunk_sizes)
        std_size = np.std(chunk_sizes)

        size_variance_penalty = min(std_size / mean_size, 1.0) if mean_size > 0 else 1.0

        optimal_size_score = 1.0 - abs(mean_size - self.optimal_chunk_size) / self.optimal_chunk_size
        optimal_size_score = max(0.0, optimal_size_score)

        return (1.0 - size_variance_penalty) * 0.5 + optimal_size_score * 0.5

    def _calculate_overlap_quality(self, chunks: List[Document]) -> float:
        if len(chunks) < 2:
            return 1.0

        overlap_scores = []
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i].page_content
            next_chunk = chunks[i + 1].page_content

            overlap_ratio = self._calculate_text_overlap(current_chunk, next_chunk)
            optimal_overlap = 0.1
            overlap_score = 1.0 - abs(overlap_ratio - optimal_overlap) / optimal_overlap
            overlap_scores.append(max(0.0, overlap_score))

        return float(np.mean(overlap_scores))

    def _calculate_information_density(self, chunks: List[Document]) -> float:
        density_scores = []

        for chunk in chunks:
            text = chunk.page_content
            word_count = len(text.split())
            char_count = len(text)

            if char_count == 0:
                density_scores.append(0.0)
                continue

            words_per_char = word_count / char_count
            sentence_count = text.count('.') + text.count('!') + text.count('?')

            if sentence_count == 0:
                avg_sentence_length = 0
            else:
                avg_sentence_length = word_count / sentence_count

            density_score = min(words_per_char * 10, 1.0)

            if avg_sentence_length > 0:
                sentence_length_score = min(avg_sentence_length / 20, 1.0)
                density_score = (density_score + sentence_length_score) / 2

            density_scores.append(density_score)

        return float(np.mean(density_scores)) if density_scores else 0.0

    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0
