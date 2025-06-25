# src/ui/components/advanced_controls.py
import streamlit as st
from typing import Dict, Any, Optional

class AdvancedControls:

    def render_chunking_controls(self, rag_system) -> Dict[str, Any]:
        st.subheader("⚙️ Chunking Parameters")

        current_size = getattr(rag_system, 'chunk_size', 1500)
        current_overlap = getattr(rag_system, 'chunk_overlap', 300)
        current_strategy = getattr(rag_system, 'chunk_strategy', 'semantic')

        chunk_size = st.slider(
            "Chunk Size",
            min_value=500,
            max_value=3000,
            value=current_size,
            step=100,
            key="chunk_size_slider"
        )

        chunk_overlap = st.slider(
            "Chunk Overlap",
            min_value=50,
            max_value=500,
            value=current_overlap,
            step=25,
            key="chunk_overlap_slider"
        )

        chunk_strategy = st.selectbox(
            "Chunking Strategy",
            options=["semantic", "recursive", "agentic_basic", "agentic_context", "agentic_adaptive", "hybrid_agentic"],
            index=self._get_strategy_index(current_strategy),
            key="chunk_strategy_select",
            help="semantic: embedding-based | recursive: rule-based | agentic_basic: LLM-guided | agentic_context: document-aware | agentic_adaptive: learning-enabled | hybrid_agentic: best of both"
        )

        st.divider()
        st.subheader("🧠 Contextual RAG Settings")

        enable_contextual = st.checkbox(
            "Enable Contextual RAG",
            value=getattr(rag_system, 'enable_contextual_rag', False),
            key="enable_contextual_rag",
            help="Use Anthropic's Contextual RAG approach for better retrieval accuracy"
        )

        if enable_contextual:
            col1, col2 = st.columns(2)
            with col1:
                dense_weight = st.slider(
                    "Dense Search Weight",
                    min_value=0.1,
                    max_value=0.9,
                    value=0.6,
                    step=0.1,
                    key="dense_weight"
                )

                use_neural_reranker = st.checkbox(
                    "Neural Reranking",
                    value=True,
                    key="use_neural_reranker"
                )

            with col2:
                sparse_weight = st.slider(
                    "Sparse Search Weight",
                    min_value=0.1,
                    max_value=0.9,
                    value=1.0 - dense_weight,
                    step=0.1,
                    key="sparse_weight",
                    disabled=True
                )

                retrieval_k = st.number_input(
                    "Final Retrieval K",
                    min_value=3,
                    max_value=15,
                    value=5,
                    key="final_retrieval_k"
                )

        if chunk_strategy == "semantic":
            threshold = st.slider(
                "Semantic Threshold",
                min_value=85,
                max_value=99,
                value=95,
                step=1,
                key="semantic_threshold"
            )
        elif chunk_strategy.startswith("agentic"):
            threshold = st.slider(
                "LLM Confidence Threshold",
                min_value=0.6,
                max_value=0.9,
                value=0.7,
                step=0.05,
                key="agentic_confidence_threshold",
                help="Higher values = more conservative chunking boundaries"
            )
        else:
            threshold = None

        contextual_params = {}
        if enable_contextual:
            contextual_params = {
                "enable_contextual_rag": enable_contextual,
                "dense_weight": dense_weight,
                "sparse_weight": sparse_weight,
                "use_neural_reranker": use_neural_reranker,
                "final_retrieval_k": retrieval_k
            }

        return {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_strategy": chunk_strategy,
            "semantic_threshold": threshold,
            **contextual_params
        }

    def render_retrieval_controls(self, rag_system) -> Dict[str, Any]:
        st.subheader("🔍 Retrieval Parameters")

        current_k = getattr(rag_system, 'retrieval_k', 6)
        current_fetch_k = getattr(rag_system, 'retrieval_fetch_k', 25)
        current_lambda = getattr(rag_system, 'retrieval_lambda_mult', 0.8)

        retrieval_k = st.slider(
            "Results Count (K)",
            min_value=2,
            max_value=20,
            value=current_k,
            step=1,
            key="retrieval_k_slider"
        )

        fetch_k = st.slider(
            "Initial Fetch Count",
            min_value=10,
            max_value=100,
            value=current_fetch_k,
            step=5,
            key="fetch_k_slider"
        )

        lambda_mult = st.slider(
            "Diversity Factor (λ)",
            min_value=0.0,
            max_value=1.0,
            value=current_lambda,
            step=0.1,
            key="lambda_mult_slider"
        )

        return {
            "retrieval_k": retrieval_k,
            "fetch_k": fetch_k,
            "lambda_mult": lambda_mult
        }

    def render_weighting_controls(self, rag_system) -> Dict[str, Any]:
        st.subheader("⚖️ Scoring Weights")

        chapter_boost = st.slider(
            "Chapter Match Boost",
            min_value=1.0,
            max_value=3.0,
            value=1.8,
            step=0.1,
            key="chapter_boost_slider"
        )

        section_boost = st.slider(
            "Section Match Boost",
            min_value=1.0,
            max_value=2.5,
            value=1.5,
            step=0.1,
            key="section_boost_slider"
        )

        pdf_boost = st.slider(
            "PDF Document Boost",
            min_value=1.0,
            max_value=2.0,
            value=1.2,
            step=0.1,
            key="pdf_boost_slider"
        )

        position_boost = st.slider(
            "Early Position Boost",
            min_value=1.0,
            max_value=1.5,
            value=1.15,
            step=0.05,
            key="position_boost_slider"
        )

        return {
            "chapter_match_boost": chapter_boost,
            "section_match_boost": section_boost,
            "pdf_document_boost": pdf_boost,
            "early_position_boost": position_boost
        }

    def render_filter_controls(self, rag_system) -> Dict[str, Any]:
        st.subheader("🎯 Content Filters")

        available_docs = rag_system.get_available_documents()

        selected_docs = st.multiselect(
            "Document Selection",
            options=available_docs,
            default=[],
            key="document_filter_select"
        )

        chapter_range = st.select_slider(
            "Chapter Range",
            options=["All", "1-5", "6-10", "11-15", "16+"],
            value="All",
            key="chapter_range_select"
        )

        min_chunk_length = st.slider(
            "Minimum Chunk Length",
            min_value=0,
            max_value=1000,
            value=100,
            step=50,
            key="min_chunk_length"
        )

        return {
            "document_filter": selected_docs,
            "chapter_range": chapter_range,
            "min_chunk_length": min_chunk_length
        }

    def render_preset_controls(self) -> Optional[str]:
        st.subheader("🎛️ Configuration Presets")

        presets = {
            "Default": "Balanced settings for general use",
            "Academic": "Optimized for academic documents",
            "Technical": "Enhanced for technical documentation",
            "Creative": "Configured for creative content",
            "Contextual RAG": "Anthropic's Contextual RAG with optimal settings",
            "Agentic + Contextual": "Smart chunking + contextual preprocessing"
        }

        selected_preset = st.selectbox(
            "Load Preset",
            options=list(presets.keys()),
            format_func=lambda x: f"{x} - {presets[x]}",
            key="preset_selector"
        )

        if st.button("Apply Preset", key="apply_preset_btn"):
            return selected_preset

        return None

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        presets = {
            "Default": {
                "chunk_size": 1500,
                "chunk_overlap": 300,
                "chunk_strategy": "semantic",
                "semantic_threshold": 95,
                "retrieval_k": 6,
                "fetch_k": 25,
                "lambda_mult": 0.8,
                "chapter_match_boost": 1.8,
                "section_match_boost": 1.5,
                "pdf_document_boost": 1.2,
                "early_position_boost": 1.15
            },
            "Academic": {
                "chunk_size": 2000,
                "chunk_overlap": 400,
                "chunk_strategy": "semantic",
                "semantic_threshold": 97,
                "retrieval_k": 8,
                "fetch_k": 30,
                "lambda_mult": 0.9,
                "chapter_match_boost": 2.2,
                "section_match_boost": 1.8,
                "pdf_document_boost": 1.4,
                "early_position_boost": 1.1
            },
            "Technical": {
                "chunk_size": 1200,
                "chunk_overlap": 200,
                "chunk_strategy": "recursive",
                "semantic_threshold": None,
                "retrieval_k": 10,
                "fetch_k": 40,
                "lambda_mult": 0.7,
                "chapter_match_boost": 1.5,
                "section_match_boost": 2.0,
                "pdf_document_boost": 1.3,
                "early_position_boost": 1.2
            },
            "Creative": {
                "chunk_size": 1800,
                "chunk_overlap": 450,
                "chunk_strategy": "semantic",
                "semantic_threshold": 92,
                "retrieval_k": 5,
                "fetch_k": 20,
                "lambda_mult": 0.6,
                "chapter_match_boost": 1.4,
                "section_match_boost": 1.3,
                "pdf_document_boost": 1.1,
                "early_position_boost": 1.3
            },
            "Contextual RAG": {
                "chunk_size": 1500,
                "chunk_overlap": 300,
                "chunk_strategy": "semantic",
                "semantic_threshold": 95,
                "retrieval_k": 6,
                "fetch_k": 25,
                "lambda_mult": 0.8,
                "chapter_match_boost": 1.8,
                "section_match_boost": 1.5,
                "pdf_document_boost": 1.2,
                "early_position_boost": 1.15,
                "enable_contextual_rag": True,
                "dense_weight": 0.6,
                "sparse_weight": 0.4,
                "use_neural_reranker": True,
                "final_retrieval_k": 5,
                "relevance_weight": 0.7,
                "original_weight": 0.3
            },
            "Agentic + Contextual": {
                "chunk_size": 1800,
                "chunk_overlap": 350,
                "chunk_strategy": "agentic_context",
                "agentic_confidence_threshold": 0.75,
                "retrieval_k": 8,
                "fetch_k": 30,
                "lambda_mult": 0.85,
                "chapter_match_boost": 2.0,
                "section_match_boost": 1.7,
                "pdf_document_boost": 1.3,
                "early_position_boost": 1.2,
                "enable_contextual_rag": True,
                "dense_weight": 0.7,
                "sparse_weight": 0.3,
                "use_neural_reranker": True,
                "final_retrieval_k": 4,
                "relevance_weight": 0.8,
                "original_weight": 0.2
            }
        }
        return presets.get(preset_name, presets["Default"])

    def _get_strategy_index(self, current_strategy: str) -> int:
        strategies = ["semantic", "recursive", "agentic_basic", "agentic_context", "agentic_adaptive", "hybrid_agentic"]
        try:
            return strategies.index(current_strategy)
        except ValueError:
            return 0
