# src/metadata/__init__.py
"""
Metadata management system for the RAG application.

This module provides centralized metadata handling including:
- Document metadata models and validation
- Content extraction and normalization
- Search and scoring metadata
- Metadata-based filtering and weighting
"""

from .models.document_metadata import DocumentMetadata, ChapterMetadata, SectionMetadata
from .extractors.chapter_extractor import ChapterExtractor
from .extractors.document_extractor import DocumentExtractor
from .managers.metadata_manager import MetadataManager
from .validators.metadata_validator import MetadataValidator

__all__ = [
    "DocumentMetadata",
    "ChapterMetadata",
    "SectionMetadata",
    "ChapterExtractor",
    "DocumentExtractor",
    "MetadataManager",
    "MetadataValidator"
]
