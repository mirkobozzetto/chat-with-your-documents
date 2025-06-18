# src/vector_stores/query_context_extractor.py
import re
from typing import Dict, Any


class QueryContextExtractor:
    """Extract context information from queries for weighted scoring"""

    def __init__(self):
        self.chapter_patterns = [
            r'chapitre\s+(\d+|[ivxlc]+)',
            r'chapter\s+(\d+|[ivxlc]+)',
            r'ch\s*(\d+)',
            r'\b(\d+)\s*(?:er|ème)\s*chapitre'
        ]

        self.section_patterns = [
            r'section\s+(\d+(?:\.\d+)?)',
            r'\b(\d+)\.(\d+)\b',
            r'partie\s+(\d+)'
        ]

        self.roman_to_arabic = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10'
        }

    def extract_context(self, query: str) -> Dict[str, Any]:
        """Extract context information from the query for weighting"""
        query_lower = query.lower()
        context = {}

        # Extract chapter references
        context.update(self._extract_chapter_references(query_lower))

        # Extract section references
        context.update(self._extract_section_references(query_lower))

        # Detect query intent/type
        context.update(self._detect_query_type(query_lower))

        return context

    def _extract_chapter_references(self, query_lower: str) -> Dict[str, str]:
        """Extract chapter references from query"""
        for pattern in self.chapter_patterns:
            match = re.search(pattern, query_lower)
            if match:
                chapter_ref = match.group(1)
                # Convert roman numerals to arabic if needed
                if chapter_ref.lower() in self.roman_to_arabic:
                    chapter_ref = self.roman_to_arabic[chapter_ref.lower()]
                return {'preferred_chapter': chapter_ref}
        return {}

    def _extract_section_references(self, query_lower: str) -> Dict[str, str]:
        """Extract section references from query"""
        for pattern in self.section_patterns:
            match = re.search(pattern, query_lower)
            if match:
                groups = match.groups()
                if len(groups) > 1 and groups[1]:  # Pattern like "1.2"
                    return {
                        'preferred_section': groups[0],
                        'preferred_subsection': groups[1]
                    }
                else:
                    return {'preferred_section': groups[0]}
        return {}

    def _detect_query_type(self, query_lower: str) -> Dict[str, str]:
        """Detect the type/intent of the query"""
        if any(word in query_lower for word in ['définition', 'definition', 'qu\'est-ce que', 'what is']):
            return {'query_type': 'definition'}
        elif any(word in query_lower for word in ['exemple', 'example', 'illustrer']):
            return {'query_type': 'example'}
        elif any(word in query_lower for word in ['comment', 'how', 'procédure', 'étapes']):
            return {'query_type': 'procedural'}
        return {}
