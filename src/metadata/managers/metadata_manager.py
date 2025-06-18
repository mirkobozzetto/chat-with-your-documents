# src/metadata/managers/metadata_manager.py
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document

from ..models.document_metadata import DocumentMetadata, ChapterMetadata, SectionMetadata
from ..models.search_metadata import QueryContext, WeightingConfig, SearchMetadata
from ..extractors.chapter_extractor import ChapterExtractor
from ..extractors.document_extractor import DocumentExtractor
from ..validators.metadata_validator import MetadataValidator


class MetadataManager:
    """Centralized metadata management for the RAG system"""

    def __init__(self, weighting_config: Optional[WeightingConfig] = None):
        self.chapter_extractor = ChapterExtractor()
        self.document_extractor = DocumentExtractor()
        self.validator = MetadataValidator()
        self.weighting_config = weighting_config or WeightingConfig()

    def process_document_chunk(self, filepath: str, content: str, chunk_index: int) -> DocumentMetadata:
        """Process a single document chunk and extract all metadata"""

        # Extract basic document metadata
        doc_metadata = self.document_extractor.create_chunk_metadata(filepath, content, chunk_index)

        # Extract chapter information
        chapter_info = self.chapter_extractor.extract_chapter_info(content)
        if chapter_info:
            doc_metadata.chapter = chapter_info

        # Extract section information
        section_info = self.chapter_extractor.extract_section_info(content)
        if section_info:
            doc_metadata.section = section_info

        # Validate metadata
        validated_metadata = self.validator.validate_and_clean(doc_metadata)

        return validated_metadata

    def process_document_with_inheritance(self, filepath: str, chunks: List[str]) -> List[DocumentMetadata]:
        """Process entire document with metadata inheritance for chunks"""

        # First, read entire document to find structural elements
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                full_content = f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            # Fallback to processing individual chunks without inheritance
            return [self.process_document_chunk(filepath, chunk, i) for i, chunk in enumerate(chunks)]

        # Extract all structural elements from full document
        structural_elements = self.chapter_extractor.find_structural_elements(full_content)

        # Process each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Try to extract metadata directly from chunk
            doc_metadata = self.process_document_chunk(filepath, chunk, i)

            # If no chapter/section found, try inheritance
            if not doc_metadata.chapter and not doc_metadata.section:
                inherited = self.chapter_extractor.inherit_metadata_from_sections(chunk, structural_elements)
                if inherited:
                    # Apply inherited metadata
                    if 'chapter_number' in inherited:
                        doc_metadata.chapter = ChapterMetadata(
                            number=inherited['chapter_number'],
                            title=inherited.get('chapter_title'),
                            raw_number=inherited.get('chapter_raw_number')
                        )

                    if 'section_number' in inherited:
                        doc_metadata.section = SectionMetadata(
                            number=inherited['section_number'],
                            title=inherited.get('section_title'),
                            level=inherited.get('section_level', 1)
                        )

                    doc_metadata.inherited_metadata = inherited.get('inherited_metadata', False)

            processed_chunks.append(doc_metadata)

        return processed_chunks

    def convert_to_langchain_documents(self, metadata_list: List[DocumentMetadata],
                                     content_list: List[str]) -> List[Document]:
        """Convert DocumentMetadata objects to LangChain Documents"""
        if len(metadata_list) != len(content_list):
            raise ValueError("Metadata list and content list must have same length")

        documents = []
        for metadata, content in zip(metadata_list, content_list):
            doc = Document(
                page_content=content,
                metadata=metadata.to_dict()
            )
            documents.append(doc)

        return documents

    def extract_from_langchain_documents(self, documents: List[Document]) -> List[DocumentMetadata]:
        """Extract DocumentMetadata from LangChain Documents"""
        metadata_list = []
        for doc in documents:
            doc_metadata = DocumentMetadata.from_dict(doc.metadata)
            metadata_list.append(doc_metadata)

        return metadata_list

    def create_search_metadata(self, base_score: float, doc_metadata: DocumentMetadata,
                             query_context: QueryContext) -> SearchMetadata:
        """Create search metadata with scoring information"""

        search_metadata = SearchMetadata(
            base_score=base_score,
            weighted_score=base_score,  # Will be updated
            query_context=query_context
        )

        # Apply chapter matching boost
        if (query_context.preferred_chapter and doc_metadata.chapter and
            query_context.preferred_chapter == doc_metadata.chapter.number):
            search_metadata.add_boost("chapter_match", self.weighting_config.chapter_match_boost)
            search_metadata.chapter_match = True

        # Apply section matching boost
        if (query_context.preferred_section and doc_metadata.section and
            query_context.preferred_section == doc_metadata.section.number):
            search_metadata.add_boost("section_match", self.weighting_config.section_match_boost)
            search_metadata.section_match = True

        # Apply document type boost
        doc_type_boost = self.weighting_config.get_boost_for_document_type(doc_metadata.document_type.value)
        if doc_type_boost > 1.0:
            search_metadata.add_boost("document_type", doc_type_boost)
            search_metadata.document_type_boost = True

        # Apply positional boost
        positional_boost = self.weighting_config.get_positional_boost(doc_metadata.chunk_index)
        if positional_boost > 1.0:
            search_metadata.add_boost("positional", positional_boost)
            search_metadata.positional_boost = True

        # Update final weighted score
        search_metadata.weighted_score = base_score * search_metadata.weight_multiplier

        return search_metadata

    def get_filter_criteria(self, query_context: QueryContext,
                          selected_document: Optional[str] = None) -> Dict[str, str]:
        """Get filter criteria for vector store searches"""
        criteria = {}

        # Document filter
        if selected_document:
            criteria["source_filename"] = selected_document

        # Context-based filters
        context_filters = query_context.get_filter_criteria()
        criteria.update(context_filters)

        return criteria

    def get_available_documents(self, all_metadata: List[DocumentMetadata]) -> List[str]:
        """Get list of available documents from metadata"""
        documents = set()
        for metadata in all_metadata:
            documents.add(metadata.source_filename)

        return sorted(list(documents))

    def get_document_stats(self, all_metadata: List[DocumentMetadata],
                         document_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for documents"""
        if document_name:
            # Stats for specific document
            doc_metadata = [m for m in all_metadata if m.source_filename == document_name]
            if not doc_metadata:
                return {"error": f"Document not found: {document_name}"}

            chapters = set()
            sections = set()
            total_chunks = len(doc_metadata)
            total_words = sum(m.word_count for m in doc_metadata)

            for m in doc_metadata:
                if m.chapter:
                    chapters.add(m.chapter.number)
                if m.section:
                    sections.add(m.section.number)

            return {
                "document": document_name,
                "total_chunks": total_chunks,
                "total_words": total_words,
                "chapters": sorted(list(chapters)),
                "sections": sorted(list(sections)),
                "document_type": doc_metadata[0].document_type.value
            }
        else:
            # Stats for all documents
            documents = {}
            for metadata in all_metadata:
                doc_name = metadata.source_filename
                if doc_name not in documents:
                    documents[doc_name] = {
                        "chunks": 0,
                        "words": 0,
                        "chapters": set(),
                        "sections": set(),
                        "type": metadata.document_type.value
                    }

                doc_stats = documents[doc_name]
                doc_stats["chunks"] += 1
                doc_stats["words"] += metadata.word_count

                if metadata.chapter:
                    doc_stats["chapters"].add(metadata.chapter.number)
                if metadata.section:
                    doc_stats["sections"].add(metadata.section.number)

            # Convert sets to sorted lists
            for doc_name, stats in documents.items():
                stats["chapters"] = sorted(list(stats["chapters"]))
                stats["sections"] = sorted(list(stats["sections"]))

            return {
                "total_documents": len(documents),
                "documents": documents
            }

    def search_metadata(self, all_metadata: List[DocumentMetadata],
                       query: str, filters: Optional[Dict[str, str]] = None) -> List[DocumentMetadata]:
        """Search metadata based on query and filters"""
        results = []

        query_lower = query.lower()

        for metadata in all_metadata:
            # Apply filters
            if filters:
                match = True
                for key, value in filters.items():
                    if key == "source_filename" and metadata.source_filename != value:
                        match = False
                        break
                    elif key == "chapter_number" and (not metadata.chapter or metadata.chapter.number != value):
                        match = False
                        break
                    elif key == "section_number" and (not metadata.section or metadata.section.number != value):
                        match = False
                        break

                if not match:
                    continue

            # Text search in metadata
            searchable_text = f"{metadata.source_filename} "
            if metadata.chapter:
                searchable_text += f"{metadata.chapter.number} {metadata.chapter.title or ''} "
            if metadata.section:
                searchable_text += f"{metadata.section.number} {metadata.section.title or ''} "

            if query_lower in searchable_text.lower():
                results.append(metadata)

        return results
