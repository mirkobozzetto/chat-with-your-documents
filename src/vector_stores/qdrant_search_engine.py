# src/vector_stores/qdrant_search_engine.py
from typing import List, Dict, Any
from .query_context_extractor import QueryContextExtractor


class QdrantSearchEngine:
    """Handle weighted scoring and search result processing for Qdrant"""

    def __init__(self):
        self.context_extractor = QueryContextExtractor()

    def apply_weighted_scoring(self, results: List[Any], query: str, search_kwargs: Dict[str, Any]) -> List[Any]:
        """Apply metadata-based weighted scoring to search results"""
        query_context = self.context_extractor.extract_context(query)
        weighted_results = []

        for result in results:
            metadata = result.payload.get('metadata', {}) if result.payload else {}
            weighted_score = self._calculate_weighted_score(
                result.score, metadata, query_context, search_kwargs
            )

            # Create a new result object with weighted score
            result.weighted_score = weighted_score
            weighted_results.append(result)

        # Sort by weighted score (higher is better)
        weighted_results.sort(key=lambda x: x.weighted_score, reverse=True)
        print(f"⚖️ Applied weighted scoring to {len(weighted_results)} results")

        return weighted_results

    def _calculate_weighted_score(self, base_score: float, metadata: Dict[str, Any],
                                 query_context: Dict[str, Any], search_kwargs: Dict[str, Any]) -> float:
        """Calculate weighted score combining vector similarity with metadata-based weights"""
        weight_multiplier = 1.0

        # Chapter relevance boost (strong signal)
        weight_multiplier *= self._apply_chapter_boost(metadata, query_context)

        # Section relevance boost
        weight_multiplier *= self._apply_section_boost(metadata, query_context)

        # Document type preferences
        weight_multiplier *= self._apply_document_type_boost(metadata)

        # Positional boost
        weight_multiplier *= self._apply_positional_boost(metadata, query_context)

        # Query type specific boosts
        weight_multiplier *= self._apply_query_type_boost(metadata, query_context)

        # Chapter title relevance
        weight_multiplier *= self._apply_chapter_title_boost(metadata, query_context)

        # Apply custom weights from search_kwargs
        weight_multiplier *= self._apply_custom_weights(metadata, search_kwargs)

        final_score = base_score * weight_multiplier

        if weight_multiplier > 1.0:
            print(f"⚖️ Score: {base_score:.3f} -> {final_score:.3f} (×{weight_multiplier:.2f})")

        return final_score

    def _apply_chapter_boost(self, metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Apply chapter matching boost"""
        if query_context.get('preferred_chapter') and metadata.get('chapter_number'):
            if str(query_context['preferred_chapter']) == str(metadata['chapter_number']):
                print(f"🎯 Chapter match boost: {metadata['chapter_number']}")
                return 1.8  # Strong boost for exact chapter match
        return 1.0

    def _apply_section_boost(self, metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Apply section matching boost"""
        multiplier = 1.0

        if query_context.get('preferred_section') and metadata.get('section_number'):
            if str(query_context['preferred_section']) == str(metadata['section_number']):
                multiplier *= 1.5
                print(f"📍 Section match boost: {metadata['section_number']}")

        if query_context.get('preferred_subsection') and metadata.get('subsection_number'):
            if str(query_context['preferred_subsection']) == str(metadata['subsection_number']):
                multiplier *= 1.3

        return multiplier

    def _apply_document_type_boost(self, metadata: Dict[str, Any]) -> float:
        """Apply document type preferences"""
        doc_type = metadata.get('document_type', '').lower()
        if doc_type == 'pdf':
            return 1.2  # PDFs often more authoritative
        elif doc_type in ['docx', 'doc']:
            return 1.1  # Word docs slightly preferred over plain text
        return 1.0

    def _apply_positional_boost(self, metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Apply positional boost for chunk position"""
        chunk_index = metadata.get('chunk_index', 0)
        if isinstance(chunk_index, int):
            if chunk_index < 5:  # First few chunks
                return 1.15
            elif chunk_index < 15:  # Early chunks
                return 1.05
        return 1.0

    def _apply_query_type_boost(self, metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Apply query type specific boosts"""
        query_type = query_context.get('query_type')
        chunk_index = metadata.get('chunk_index', 0)

        if query_type == 'definition' and chunk_index < 10:
            return 1.2  # Definitions often in early content
        elif query_type == 'example' and metadata.get('section_title', '').lower().find('exemple') != -1:
            return 1.3  # Boost sections with "exemple" in title
        return 1.0

    def _apply_chapter_title_boost(self, metadata: Dict[str, Any], query_context: Dict[str, Any]) -> float:
        """Apply chapter title relevance boost"""
        chapter_title = metadata.get('chapter_title', '').lower()
        if chapter_title and query_context.get('preferred_chapter'):
            # Basic keyword matching in chapter titles
            query_words = set(query_context.get('query_keywords', []))
            title_words = set(chapter_title.split())
            if query_words.intersection(title_words):
                return 1.1
        return 1.0

    def _apply_custom_weights(self, metadata: Dict[str, Any], search_kwargs: Dict[str, Any]) -> float:
        """Apply custom weights from search_kwargs"""
        custom_weights = search_kwargs.get('metadata_weights', {})
        multiplier = 1.0

        for metadata_key, weight_factor in custom_weights.items():
            if metadata.get(metadata_key):
                multiplier *= weight_factor

        return multiplier
