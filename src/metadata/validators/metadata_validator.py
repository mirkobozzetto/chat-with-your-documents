# src/metadata/validators/metadata_validator.py
import re
from typing import Optional, List, Dict, Any
from ..models.document_metadata import DocumentMetadata, ChapterMetadata, SectionMetadata


class MetadataValidator:
    """Validate and clean metadata for consistency and quality"""

    def __init__(self):
        self.max_title_length = 200
        self.min_title_length = 3
        self.valid_chapter_pattern = re.compile(r'^[0-9]+$|^[ivxlc]+$', re.IGNORECASE)
        self.valid_section_pattern = re.compile(r'^[0-9]+(\.[0-9]+)*$')

    def validate_and_clean(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Validate and clean all metadata fields"""

        # Clean chapter metadata
        if metadata.chapter:
            metadata.chapter = self._validate_chapter(metadata.chapter)

        # Clean section metadata
        if metadata.section:
            metadata.section = self._validate_section(metadata.section)

        # Validate basic fields
        metadata = self._validate_basic_fields(metadata)

        # Clean custom fields
        metadata.custom_fields = self._clean_custom_fields(metadata.custom_fields)

        return metadata

    def _validate_chapter(self, chapter: ChapterMetadata) -> Optional[ChapterMetadata]:
        """Validate and clean chapter metadata"""

        # Validate chapter number
        if not self._is_valid_chapter_number(chapter.number):
            return None

        # Clean chapter title
        cleaned_title = self._clean_title(chapter.title) if chapter.title else None

        return ChapterMetadata(
            number=chapter.number,
            title=cleaned_title,
            raw_number=chapter.raw_number
        )

    def _validate_section(self, section: SectionMetadata) -> Optional[SectionMetadata]:
        """Validate and clean section metadata"""

        # Validate section number format
        if not self.valid_section_pattern.match(section.number):
            return None

        # Validate level
        if section.level < 1 or section.level > 5:
            section.level = min(max(section.level, 1), 5)

        # Clean section title
        cleaned_title = self._clean_title(section.title) if section.title else None

        return SectionMetadata(
            number=section.number,
            subsection=section.subsection,
            title=cleaned_title,
            level=section.level
        )

    def _validate_basic_fields(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Validate basic document fields"""

        # Ensure chunk_index is non-negative
        if metadata.chunk_index < 0:
            metadata.chunk_index = 0

        # Ensure content_length and word_count are non-negative
        if metadata.content_length < 0:
            metadata.content_length = 0

        if metadata.word_count < 0:
            metadata.word_count = 0

        # Clean filename
        metadata.source_filename = self._clean_filename(metadata.source_filename)

        return metadata

    def _is_valid_chapter_number(self, chapter_number: str) -> bool:
        """Check if chapter number is in valid format"""
        if not chapter_number:
            return False

        # Allow digits or roman numerals
        return bool(self.valid_chapter_pattern.match(chapter_number.strip()))

    def _clean_title(self, title: Optional[str]) -> Optional[str]:
        """Clean and validate titles"""
        if not title:
            return None

        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title.strip())

        # Remove problematic characters but keep basic punctuation
        title = re.sub(r'[^\w\s\-–—\'\"().,!?:;]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()

        # Check length constraints
        if len(title) < self.min_title_length or len(title) > self.max_title_length:
            return None

        # Check if title has reasonable content (not just numbers/symbols)
        alpha_ratio = sum(c.isalpha() for c in title) / len(title)
        if alpha_ratio < 0.3:  # At least 30% letters
            return None

        return title

    def _clean_filename(self, filename: str) -> str:
        """Clean filename for consistency"""
        if not filename:
            return "unknown"

        # Remove any path components, keep just filename
        filename = filename.split('/')[-1].split('\\')[-1]

        # Ensure it's not empty
        if not filename.strip():
            return "unknown"

        return filename.strip()

    def _clean_custom_fields(self, custom_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Clean custom metadata fields"""
        cleaned = {}

        for key, value in custom_fields.items():
            # Clean key
            clean_key = re.sub(r'[^\w_]', '_', key.strip().lower())
            if not clean_key:
                continue

            # Clean value based on type
            if isinstance(value, str):
                clean_value = value.strip()
                if len(clean_value) > 1000:  # Limit string length
                    clean_value = clean_value[:1000]
                cleaned[clean_key] = clean_value
            elif isinstance(value, (int, float, bool)):
                cleaned[clean_key] = value
            elif value is None:
                cleaned[clean_key] = None
            else:
                # Convert other types to string
                cleaned[clean_key] = str(value)[:1000]

        return cleaned

    def validate_metadata_consistency(self, metadata_list: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Validate consistency across multiple metadata objects"""
        issues = []

        # Group by document
        documents = {}
        for metadata in metadata_list:
            doc_name = metadata.source_filename
            if doc_name not in documents:
                documents[doc_name] = []
            documents[doc_name].append(metadata)

        # Check each document for consistency
        for doc_name, doc_metadata in documents.items():
            doc_issues = self._check_document_consistency(doc_name, doc_metadata)
            issues.extend(doc_issues)

        return issues

    def _check_document_consistency(self, doc_name: str,
                                  metadata_list: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Check consistency within a single document"""
        issues = []

        # Check chunk index sequence
        chunk_indices = [m.chunk_index for m in metadata_list]
        expected_indices = list(range(len(metadata_list)))

        if sorted(chunk_indices) != expected_indices:
            issues.append({
                "type": "chunk_index_inconsistency",
                "document": doc_name,
                "message": f"Chunk indices not sequential: {chunk_indices}"
            })

        # Check for duplicate chunk indices
        if len(set(chunk_indices)) != len(chunk_indices):
            issues.append({
                "type": "duplicate_chunk_index",
                "document": doc_name,
                "message": "Duplicate chunk indices found"
            })

        # Check document type consistency
        doc_types = set(m.document_type for m in metadata_list)
        if len(doc_types) > 1:
            issues.append({
                "type": "inconsistent_document_type",
                "document": doc_name,
                "message": f"Multiple document types: {doc_types}"
            })

        # Check chapter number sequence (if chapters exist)
        chapters_with_indices = [(m.chunk_index, m.chapter.number)
                               for m in metadata_list if m.chapter]

        if chapters_with_indices:
            # Sort by chunk index
            chapters_with_indices.sort()

            # Check for logical chapter progression
            prev_chapter = None
            for chunk_idx, chapter_num in chapters_with_indices:
                if prev_chapter and chapter_num != prev_chapter:
                    # Chapter changed - should be sequential
                    try:
                        if int(chapter_num) != int(prev_chapter) + 1:
                            issues.append({
                                "type": "non_sequential_chapters",
                                "document": doc_name,
                                "message": f"Chapter {chapter_num} follows {prev_chapter} at chunk {chunk_idx}"
                            })
                    except ValueError:
                        # Non-numeric chapters, skip sequence check
                        pass
                prev_chapter = chapter_num

        return issues

    def get_validation_report(self, metadata_list: List[DocumentMetadata]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        total_items = len(metadata_list)
        valid_items = 0
        issues = []

        # Validate individual items
        for i, metadata in enumerate(metadata_list):
            item_issues = []

            # Check required fields
            if not metadata.source_filename:
                item_issues.append("Missing source filename")

            if metadata.chunk_index < 0:
                item_issues.append("Invalid chunk index")

            # Check chapter validity
            if metadata.chapter and not self._is_valid_chapter_number(metadata.chapter.number):
                item_issues.append("Invalid chapter number format")

            # Check section validity
            if metadata.section and not self.valid_section_pattern.match(metadata.section.number):
                item_issues.append("Invalid section number format")

            if item_issues:
                issues.append({
                    "item_index": i,
                    "document": metadata.source_filename,
                    "chunk_index": metadata.chunk_index,
                    "issues": item_issues
                })
            else:
                valid_items += 1

        # Check consistency across items
        consistency_issues = self.validate_metadata_consistency(metadata_list)

        return {
            "total_items": total_items,
            "valid_items": valid_items,
            "invalid_items": total_items - valid_items,
            "validation_rate": valid_items / total_items if total_items > 0 else 0,
            "individual_issues": issues,
            "consistency_issues": consistency_issues,
            "summary": {
                "documents_processed": len(set(m.source_filename for m in metadata_list)),
                "chapters_found": len(set(m.chapter.number for m in metadata_list if m.chapter)),
                "sections_found": len(set(m.section.number for m in metadata_list if m.section)),
                "inherited_metadata_count": sum(1 for m in metadata_list if m.inherited_metadata)
            }
        }
