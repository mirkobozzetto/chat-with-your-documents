# src/quality/simple_chunk_evaluator.py
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.schema import Document
import re


@dataclass
class SimpleQualityScore:
    size_consistency: float
    content_density: float
    overall_score: float


class SimpleChunkEvaluator:

    def __init__(self):
        self.min_chunk_size = 100
        self.max_chunk_size = 2000
        self.optimal_chunk_size = 1000

    def evaluate_chunks(self, chunks: List[Document]) -> SimpleQualityScore:
        if not chunks:
            return SimpleQualityScore(0.0, 0.0, 0.0)

        size_score = self._calculate_size_consistency(chunks)
        density_score = self._calculate_content_density(chunks)

        overall_score = (size_score * 0.6 + density_score * 0.4)

        return SimpleQualityScore(
            size_consistency=size_score,
            content_density=density_score,
            overall_score=overall_score
        )

    def _calculate_size_consistency(self, chunks: List[Document]) -> float:
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]

        if not chunk_sizes:
            return 0.0

        mean_size = sum(chunk_sizes) / len(chunk_sizes)

        if mean_size == 0:
            return 0.0

        variance = sum((size - mean_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        std_dev = variance ** 0.5

        size_variance_penalty = min(std_dev / mean_size, 1.0)

        optimal_size_score = 1.0 - abs(mean_size - self.optimal_chunk_size) / self.optimal_chunk_size
        optimal_size_score = max(0.0, optimal_size_score)

        return (1.0 - size_variance_penalty) * 0.5 + optimal_size_score * 0.5

    def _calculate_content_density(self, chunks: List[Document]) -> float:
        density_scores = []

        for chunk in chunks:
            text = chunk.page_content

            word_count = len(text.split())
            char_count = len(text)

            if char_count == 0:
                density_scores.append(0.0)
                continue

            words_per_char = word_count / char_count

            sentence_count = len(re.findall(r'[.!?]+', text))

            if sentence_count == 0:
                avg_sentence_length = 0
            else:
                avg_sentence_length = word_count / sentence_count

            density_score = min(words_per_char * 10, 1.0)

            if avg_sentence_length > 0:
                sentence_length_score = min(avg_sentence_length / 20, 1.0)
                density_score = (density_score + sentence_length_score) / 2

            density_scores.append(density_score)

        return sum(density_scores) / len(density_scores) if density_scores else 0.0
