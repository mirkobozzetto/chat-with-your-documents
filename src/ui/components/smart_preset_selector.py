# src/ui/components/smart_preset_selector.py
import streamlit as st
import pandas as pd
import os
from typing import Dict, Any, Optional
from pathlib import Path

class SmartPresetSelector:

    def __init__(self):
        self.presets = {
            "standard": {
                "display_name": "Standard",
                "description": "Reliable chunking, guaranteed scoring",
                "technical_details": "Recursive chunking, no AI",
                "processing_time": "Fast (30s - 2min)",
                "use_cases": [
                    "Normal PDF documents (<200 pages)",
                    "System testing",
                    "Daily workflow"
                ],
                "config": {
                    "chunk_strategy": "recursive",
                    "chunk_size": 1200,
                    "chunk_overlap": 200,
                    "enable_contextual_rag": False,
                    "use_neural_reranker": False,
                    "retrieval_k": 6,
                    "fetch_k": 25,
                    "lambda_mult": 0.8
                },
                "quality_score_expected": "0.65-0.75",
                "complexity": "simple"
            },

            "premium": {
                "display_name": "Premium",
                "description": "Smart chunking for large files",
                "technical_details": "LLM analyzes structure before splitting",
                "processing_time": "Medium (3-8 min)",
                "use_cases": [
                    "Books and documents >200 pages",
                    "Complex structured documents",
                    "When chunking precision is critical"
                ],
                "config": {
                    "chunk_strategy": "agentic_context",
                    "chunk_size": 1500,
                    "chunk_overlap": 250,
                    "enable_contextual_rag": False,
                    "use_neural_reranker": True,
                    "retrieval_k": 8,
                    "fetch_k": 30,
                    "lambda_mult": 0.85
                },
                "quality_score_expected": "0.70-0.80",
                "complexity": "advanced",
                "warning": "Uses LLM calls to analyze structure"
            },

            "ultra": {
                "display_name": "Ultra",
                "description": "Contextual search for critical cases",
                "technical_details": "Contextual RAG + Neural reranking",
                "processing_time": "Slow (5-15 min)",
                "use_cases": [
                    "Very complex documents >500 pages",
                    "Maximum precision search",
                    "Critical applications (medical, legal)"
                ],
                "config": {
                    "chunk_strategy": "agentic_context",
                    "chunk_size": 1200,
                    "chunk_overlap": 200,
                    "enable_contextual_rag": True,
                    "use_neural_reranker": True,
                    "dense_weight": 0.7,
                    "sparse_weight": 0.3,
                    "retrieval_k": 5,
                    "fetch_k": 20,
                    "lambda_mult": 0.9
                },
                "quality_score_expected": "0.75-0.85",
                "complexity": "expert",
                "warning": "Most intensive processing - LLM + contextual preprocessing"
            }
        }

    def analyze_document_requirements(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"recommended_preset": "standard", "reasoning": "Fichier non trouvé"}

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            estimated_pages = file_size_mb * 20
        elif file_ext in ['.docx', '.doc']:
            estimated_pages = file_size_mb * 50
        else:
            estimated_pages = file_size_mb * 100

        if estimated_pages > 500:
            return {
                "recommended_preset": "ultra",
                "reasoning": f"Very large document detected (~{estimated_pages:.0f} pages)",
                "document_size": f"{file_size_mb:.1f} MB",
                "estimated_pages": int(estimated_pages),
                "complexity_detected": "very high"
            }
        elif estimated_pages > 200 or file_size_mb > 10:
            return {
                "recommended_preset": "premium",
                "reasoning": f"Large document detected (~{estimated_pages:.0f} pages)",
                "document_size": f"{file_size_mb:.1f} MB",
                "estimated_pages": int(estimated_pages),
                "complexity_detected": "high"
            }
        else:
            return {
                "recommended_preset": "standard",
                "reasoning": f"Standard size document (~{estimated_pages:.0f} pages)",
                "document_size": f"{file_size_mb:.1f} MB",
                "estimated_pages": int(estimated_pages),
                "complexity_detected": "normal"
            }

    def render_document_analysis(self, file_path: str) -> None:
        if not file_path:
            return

        try:
            analysis = self.analyze_document_requirements(file_path)

            st.subheader("Document Analysis")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Size", analysis.get("document_size", "Unknown"))
            with col2:
                st.metric("Estimated pages", analysis.get("estimated_pages", 0))
            with col3:
                st.metric("Complexity", analysis.get("complexity_detected", "Unknown"))

            recommended = analysis.get("recommended_preset", "standard")
            preset_info = self.presets.get(recommended, self.presets["standard"])

            st.success(f"**Recommended:** {preset_info['display_name']}")
            st.info(f"**Reason:** {analysis.get('reasoning', 'Default analysis')}")
        except Exception as e:
            st.error(f"Document analysis error: {str(e)}")
            st.info("Using Standard preset as default")

    def render_preset_selection(self, recommended_preset: str = "standard") -> Optional[str]:
        st.subheader("Processing Mode Selection")

        selected_preset = None

        for preset_key, preset in self.presets.items():
            if preset_key == recommended_preset:
                st.markdown(f"**{preset['display_name']} (Recommended)**")
            else:
                st.markdown(f"**{preset['display_name']}**")
            
            st.write(f"*{preset['description']}*")
            st.write(f"⏱️ {preset['processing_time']} | 🎯 {preset['quality_score_expected']}")
            
            if preset.get("warning"):
                st.warning(preset['warning'])
                cost_warning = self._get_cost_warning(preset_key)
                if cost_warning:
                    st.error(f"💰 {cost_warning}")

            if st.button(
                f"Use {preset['display_name']}",
                key=f"btn_{preset_key}",
                type="primary" if preset_key == recommended_preset else "secondary",
                use_container_width=True
            ):
                selected_preset = preset_key
            
            st.divider()

        return selected_preset

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        return self.presets.get(preset_name, self.presets["standard"])["config"]

    def render_smart_interface(self, file_path: str = None) -> Optional[str]:
        st.title("Smart Preset Selection")

        recommended = "standard"
        if file_path:
            try:
                self.render_document_analysis(file_path)
                analysis = self.analyze_document_requirements(file_path)
                recommended = analysis.get("recommended_preset", "standard")
                st.divider()
            except Exception as e:
                st.warning(f"Cannot analyze file: {str(e)}")
                st.info("Using standard mode as default")

        return self.render_preset_selection(recommended)

    def render_comparison_table(self) -> None:
        st.subheader("Preset Details")
        
        for preset_key, preset in self.presets.items():
            st.markdown(f"**{preset['display_name']}** - {preset['description']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Technical:** {preset['technical_details']}")
                st.write(f"**Processing time:** {preset['processing_time']}")
                st.write(f"**Quality score:** {preset['quality_score_expected']}")
                st.write(f"**Complexity:** {preset['complexity'].title()}")
            
            with col2:
                st.write("**Ideal for:**")
                for use_case in preset["use_cases"]:
                    st.write(f"• {use_case}")
            
            st.divider()

    def _get_cost_warning(self, preset_key: str) -> str:
        cost_estimates = {
            "standard": "",
            "premium": "~$0.10-0.50 per document (LLM chunking)",
            "ultra": "~$0.50-2.00 per document (LLM + contextual processing)"
        }
        return cost_estimates.get(preset_key, "")
