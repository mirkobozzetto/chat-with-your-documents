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
            options=["semantic", "recursive"],
            index=0 if current_strategy == "semantic" else 1,
            key="chunk_strategy_select"
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
        else:
            threshold = None

        return {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunk_strategy": chunk_strategy,
            "semantic_threshold": threshold
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
            "Creative": "Configured for creative content"
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
            }
        }
        return presets.get(preset_name, presets["Default"])
