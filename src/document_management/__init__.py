# src/document_management/__init__.py
"""
Document Management Module

This module contains all document-related functionality:
- DocumentProcessor: Handles document loading and chunking
- DocumentSelector: Handles document filtering logic
- DocumentSelectionPersistence: Manages document selection persistence
"""

from .document_processor import DocumentProcessor
from .document_selector import DocumentSelector
from .document_selection_persistence import DocumentSelectionPersistence

__all__ = [
    'DocumentProcessor',
    'DocumentSelector',
    'DocumentSelectionPersistence'
]
