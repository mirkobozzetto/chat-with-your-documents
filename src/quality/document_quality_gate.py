# src/quality/document_quality_gate.py
from typing import List, Dict, Any, Tuple
from pathlib import Path
from langchain.schema import Document
import streamlit as st

from .quality_validator import QualityValidator, ValidationResult


class DocumentQualityGate:

    def __init__(self, min_score_threshold: float = 0.6, enable_empirical_validation: bool = False):
        self.validator = QualityValidator()
        self.validator.thresholds.min_overall_score = min_score_threshold
        self.enable_empirical_validation = enable_empirical_validation

        print(f"🛡️ Quality Gate initialized (threshold: {min_score_threshold:.3f})", flush=True)
        if enable_empirical_validation:
            print("🧪 Empirical validation enabled (simplified mode)", flush=True)

        self.processing_stats = {
            "total_processed": 0,
            "accepted": 0,
            "rejected": 0,
            "rejection_reasons": {}
        }

    def validate_before_vectorization(self, chunks: List[Document],
                                    document_path: str) -> Tuple[bool, ValidationResult]:
        self.processing_stats["total_processed"] += 1

        print(f"\n🛡️ === QUALITY GATE ANALYSIS ===", flush=True)
        print(f"📄 Document: {Path(document_path).name}", flush=True)
        print(f"📊 Chunks to evaluate: {len(chunks)}", flush=True)

        validation_result = self.validator.validate_chunks(chunks, document_path)
        score = validation_result.quality_score

        # Also show in Streamlit
        st.info(f"🛡️ **Quality Gate:** Analyzing {len(chunks)} chunks for {Path(document_path).name}")

        print(f"\n📈 QUALITY SCORES:", flush=True)
        if hasattr(score, 'semantic_coherence'):
            print(f"   • Semantic Coherence: {score.semantic_coherence:.3f}", flush=True)
        if hasattr(score, 'size_consistency'):
            print(f"   • Size Consistency: {score.size_consistency:.3f}", flush=True)
        if hasattr(score, 'overlap_quality'):
            print(f"   • Overlap Quality: {score.overlap_quality:.3f}", flush=True)
        if hasattr(score, 'information_density'):
            print(f"   • Information Density: {score.information_density:.3f}", flush=True)
        if hasattr(score, 'content_density'):
            print(f"   • Content Density: {score.content_density:.3f}", flush=True)
        print(f"   • OVERALL SCORE: {score.overall_score:.3f}", flush=True)

        threshold = self.validator.thresholds.min_overall_score
        print(f"🎯 Threshold: {threshold:.3f}", flush=True)

        # Show scores in Streamlit
        with st.expander("📊 Quality Scores", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                if hasattr(score, 'semantic_coherence'):
                    st.metric("Semantic Coherence", f"{score.semantic_coherence:.3f}")
                if hasattr(score, 'size_consistency'):
                    st.metric("Size Consistency", f"{score.size_consistency:.3f}")
            with col2:
                if hasattr(score, 'information_density'):
                    st.metric("Information Density", f"{score.information_density:.3f}")
                if hasattr(score, 'content_density'):
                    st.metric("Content Density", f"{score.content_density:.3f}")

            threshold = self.validator.thresholds.min_overall_score
            st.metric("**OVERALL SCORE**", f"{score.overall_score:.3f}",
                     delta=f"Threshold: {threshold:.3f}")

        if validation_result.is_valid:
            self.processing_stats["accepted"] += 1
            print(f"✅ DECISION: APPROVED FOR VECTORIZATION", flush=True)
            st.success(f"✅ **Quality Gate PASSED** (Score: {score.overall_score:.3f})")

            if validation_result.recommendations:
                print(f"💡 Suggestions for improvement:", flush=True)
                with st.expander("💡 Suggestions for Improvement"):
                    for rec in validation_result.recommendations:
                        print(f"   • {rec}", flush=True)
                        st.write(f"• {rec}")
            print(f"🛡️ === END QUALITY GATE ===\n", flush=True)
            return True, validation_result
        else:
            self.processing_stats["rejected"] += 1
            self._record_rejection_reasons(validation_result.rejection_reasons)
            print(f"❌ DECISION: REJECTED", flush=True)
            st.error(f"❌ **Quality Gate FAILED** (Score: {score.overall_score:.3f})")

            print(f"🚫 Rejection reasons:", flush=True)
            with st.expander("🚫 Rejection Reasons", expanded=True):
                for reason in validation_result.rejection_reasons:
                    print(f"   • {reason}", flush=True)
                    st.write(f"• {reason}")

            print(f"💡 Recommendations:", flush=True)
            with st.expander("💡 How to Fix"):
                for rec in validation_result.recommendations:
                    print(f"   • {rec}", flush=True)
                    st.write(f"• {rec}")
            print(f"🛡️ === END QUALITY GATE ===\n", flush=True)
            return False, validation_result

    def get_processing_statistics(self) -> Dict[str, Any]:
        total = self.processing_stats["total_processed"]
        if total == 0:
            return {"status": "no_documents_processed"}

        return {
            "total_documents": total,
            "acceptance_rate": self.processing_stats["accepted"] / total,
            "rejection_rate": self.processing_stats["rejected"] / total,
            "most_common_rejections": self._get_top_rejection_reasons()
        }

    def reset_statistics(self):
        self.processing_stats = {
            "total_processed": 0,
            "accepted": 0,
            "rejected": 0,
            "rejection_reasons": {}
        }

    def _record_rejection_reasons(self, reasons: List[str]):
        for reason in reasons:
            key = reason.split(":")[0]
            self.processing_stats["rejection_reasons"][key] = (
                self.processing_stats["rejection_reasons"].get(key, 0) + 1
            )

    def _get_top_rejection_reasons(self) -> List[Tuple[str, int]]:
        reasons = self.processing_stats["rejection_reasons"]
        return sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:3]
