# src/ui/components/smart_preset_selector.py
import streamlit as st
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
        """Analyse un document et recommande le preset optimal"""
        if not os.path.exists(file_path):
            return {"recommended_preset": "standard", "reasoning": "Fichier non trouvé"}
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        file_ext = Path(file_path).suffix.lower()
        
        # Estimation grossière du nombre de pages
        if file_ext == '.pdf':
            estimated_pages = file_size_mb * 20  # ~20 pages par MB pour PDF
        elif file_ext in ['.docx', '.doc']:
            estimated_pages = file_size_mb * 50  # ~50 pages par MB pour Word
        else:
            estimated_pages = file_size_mb * 100  # Texte brut
        
        # Logique de recommandation
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
        """Affiche l'analyse du document avec recommandation"""
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
            
            # Recommandation
            recommended = analysis.get("recommended_preset", "standard")
            preset_info = self.presets.get(recommended, self.presets["standard"])
            
            st.success(f"**Recommended:** {preset_info['display_name']}")
            st.info(f"**Reason:** {analysis.get('reasoning', 'Default analysis')}")
        except Exception as e:
            st.error(f"Document analysis error: {str(e)}")
            st.info("Using Standard preset as default")

    def render_preset_selection(self, recommended_preset: str = "standard") -> Optional[str]:
        """Interface de sélection des presets avec détails"""
        st.subheader("Processing Mode Selection")
        
        selected_preset = None
        
        for preset_key, preset in self.presets.items():
            # Highlight si recommandé
            if preset_key == recommended_preset:
                st.markdown(f"### {preset['display_name']} (Recommended)")
            else:
                st.markdown(f"### {preset['display_name']}")
            
            with st.expander(f"Details {preset['display_name']}", expanded=(preset_key == recommended_preset)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {preset['description']}")
                    st.write(f"**Technical:** {preset['technical_details']}")
                    st.write(f"**Processing time:** {preset['processing_time']}")
                    st.write(f"**Expected quality score:** {preset['quality_score_expected']}")
                    
                    st.write("**Ideal for:**")
                    for use_case in preset["use_cases"]:
                        st.write(f"• {use_case}")
                    
                    # Warning si complexe
                    if preset.get("warning"):
                        st.warning(preset['warning'])
                
                with col2:
                    if st.button(
                        f"Use {preset['display_name']}", 
                        key=f"btn_{preset_key}",
                        type="primary" if preset_key == recommended_preset else "secondary"
                    ):
                        if preset["complexity"] in ["advanced", "expert"]:
                            with st.form(f"confirm_{preset_key}"):
                                st.warning(f"{preset['display_name']} mode selected")
                                st.write(preset.get("warning", ""))
                                if st.form_submit_button("Confirm"):
                                    selected_preset = preset_key
                        else:
                            selected_preset = preset_key
        
        return selected_preset

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """Retourne la configuration complète d'un preset"""
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
        """Tableau comparatif des presets"""
        st.subheader("Preset Comparison")
        
        import pandas as pd
        
        data = []
        for key, preset in self.presets.items():
            data.append({
                "Preset": preset["display_name"],
                "Complexity": preset["complexity"].title(),
                "Time": preset["processing_time"],
                "Quality Score": preset["quality_score_expected"],
                "Use Case": preset["use_cases"][0]
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)