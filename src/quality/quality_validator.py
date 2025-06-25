# src/quality/quality_validator.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.schema import Document
try:
    from .chunk_quality_evaluator import ChunkQualityEvaluator, ChunkQualityScore
except ImportError:
    from .simple_chunk_evaluator import SimpleChunkEvaluator as ChunkQualityEvaluator, SimpleQualityScore as ChunkQualityScore
    print("⚠️ Using simplified chunk evaluator (no sentence-transformers)")


@dataclass
class QualityThresholds:
    min_semantic_coherence: float = 0.4
    min_size_consistency: float = 0.3
    min_overlap_quality: float = 0.3
    min_information_density: float = 0.25
    min_overall_score: float = 0.4


@dataclass
class ValidationResult:
    is_valid: bool
    quality_score: ChunkQualityScore
    rejection_reasons: List[str]
    recommendations: List[str]


class QualityValidator:

    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        self.thresholds = thresholds or QualityThresholds()
        self.evaluator = ChunkQualityEvaluator()

    def validate_chunks(self, chunks: List[Document], document_name: str = "") -> ValidationResult:
        quality_score = self.evaluator.evaluate_chunks(chunks)

        rejection_reasons = self._identify_rejection_reasons(quality_score)
        recommendations = self._generate_recommendations(quality_score, chunks)

        is_valid = len(rejection_reasons) == 0

        return ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            rejection_reasons=rejection_reasons,
            recommendations=recommendations
        )

    def _identify_rejection_reasons(self, score: ChunkQualityScore) -> List[str]:
        reasons = []

        if score.semantic_coherence < self.thresholds.min_semantic_coherence:
            reasons.append(f"Faible cohérence sémantique: {score.semantic_coherence:.3f}")

        if score.size_consistency < self.thresholds.min_size_consistency:
            reasons.append(f"Tailles de chunks incohérentes: {score.size_consistency:.3f}")

        if score.overlap_quality < self.thresholds.min_overlap_quality:
            reasons.append(f"Qualité de chevauchement insuffisante: {score.overlap_quality:.3f}")

        if score.information_density < self.thresholds.min_information_density:
            reasons.append(f"Densité d'information trop faible: {score.information_density:.3f}")

        if score.overall_score < self.thresholds.min_overall_score:
            reasons.append(f"Score global insuffisant: {score.overall_score:.3f}")

        return reasons

    def _generate_recommendations(self, score: ChunkQualityScore, chunks: List[Document]) -> List[str]:
        recommendations = []

        if score.semantic_coherence < 0.7:
            recommendations.append("Utiliser chunking sémantique au lieu de récursif")

        if score.size_consistency < 0.6:
            chunk_sizes = [len(chunk.page_content) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0

            if avg_size < 500:
                recommendations.append("Augmenter la taille des chunks (chunk_size)")
            elif avg_size > 1500:
                recommendations.append("Réduire la taille des chunks")

        if score.overlap_quality < 0.5:
            recommendations.append("Ajuster le chunk_overlap (recommandé: 10-20% de chunk_size)")

        if score.information_density < 0.4:
            recommendations.append("Document peu informatif - considérer un prétraitement")

        if not recommendations:
            recommendations.append("Qualité acceptable - peut être vectorisé")

        return recommendations

    def should_vectorize(self, chunks: List[Document]) -> bool:
        validation_result = self.validate_chunks(chunks)
        return validation_result.is_valid

    def suggest_chunking_parameters(self, chunks: List[Document]) -> Dict[str, int]:
        validation_result = self.validate_chunks(chunks)
        score = validation_result.quality_score

        return self._suggest_parameters(score, chunks)

    def _recommend_strategy(self, score: ChunkQualityScore) -> str:
        if score.semantic_coherence < 0.5:
            return "semantic"
        elif score.size_consistency < 0.5:
            return "recursive"
        else:
            return "current"

    def _suggest_parameters(self, score: ChunkQualityScore, chunks: List[Document]) -> Dict[str, int]:
        if not chunks:
            return {}

        current_avg_size = sum(len(chunk.page_content) for chunk in chunks) / len(chunks)

        suggested_size = int(current_avg_size)
        suggested_overlap = int(current_avg_size * 0.15)

        if score.size_consistency < 0.6:
            if current_avg_size < 800:
                suggested_size = 1000
            elif current_avg_size > 1200:
                suggested_size = 800

        if score.overlap_quality < 0.5:
            suggested_overlap = max(int(suggested_size * 0.1), 100)

        return {
            "chunk_size": suggested_size,
            "chunk_overlap": suggested_overlap
        }
