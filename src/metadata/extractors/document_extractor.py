# src/metadata/extractors/document_extractor.py
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.document_metadata import DocumentType, DocumentMetadata


class DocumentExtractor:
    """Extract basic document metadata from file properties and content"""

    def __init__(self):
        self.supported_extensions = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.DOC,
            '.txt': DocumentType.TXT,
            '.md': DocumentType.MD,
            '.html': DocumentType.HTML,
            '.htm': DocumentType.HTML
        }

    def extract_from_filepath(self, filepath: str) -> Dict[str, Any]:
        """Extract metadata from file path and properties"""
        path = Path(filepath)

        # Basic file information
        filename = path.name
        file_ext = path.suffix.lower()

        # Determine document type
        doc_type = self.supported_extensions.get(file_ext, DocumentType.TXT)

        metadata = {
            "source_filename": filename,
            "document_type": doc_type.value,
            "file_path": str(path),
            "file_extension": file_ext
        }

        # Add file stats if file exists
        if path.exists():
            stat = path.stat()
            metadata.update({
                "file_size": stat.st_size,
                "created_timestamp": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return metadata

    def extract_from_content(self, content: str) -> Dict[str, Any]:
        """Extract metadata from document content"""
        if not content:
            return {"content_length": 0, "word_count": 0}

        # Basic content statistics
        content_length = len(content)
        words = content.split()
        word_count = len(words)

        # Character statistics
        char_stats = self._analyze_characters(content)

        # Language detection (basic)
        detected_language = self._detect_language_simple(content)

        metadata = {
            "content_length": content_length,
            "word_count": word_count,
            "line_count": content.count('\n') + 1,
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "detected_language": detected_language,
            **char_stats
        }

        return metadata

    def create_chunk_metadata(self, filepath: str, content: str, chunk_index: int,
                            additional_metadata: Optional[Dict[str, Any]] = None) -> DocumentMetadata:
        """Create complete metadata for a document chunk"""

        # Extract file-based metadata
        file_metadata = self.extract_from_filepath(filepath)

        # Extract content-based metadata
        content_metadata = self.extract_from_content(content)

        # Combine all metadata
        combined_metadata = {
            **file_metadata,
            **content_metadata,
            "chunk_index": chunk_index,
            "processing_timestamp": datetime.now().isoformat()
        }

        # Add any additional metadata
        if additional_metadata:
            combined_metadata.update(additional_metadata)

        # Create DocumentMetadata object
        return DocumentMetadata(
            source_filename=combined_metadata["source_filename"],
            document_type=DocumentType(combined_metadata["document_type"]),
            chunk_index=chunk_index,
            content_length=combined_metadata["content_length"],
            word_count=combined_metadata["word_count"],
            processing_timestamp=combined_metadata["processing_timestamp"],
            custom_fields={k: v for k, v in combined_metadata.items()
                          if k not in ["source_filename", "document_type", "chunk_index",
                                     "content_length", "word_count", "processing_timestamp"]}
        )

    def _analyze_characters(self, content: str) -> Dict[str, Any]:
        """Analyze character composition of content"""
        if not content:
            return {"alpha_ratio": 0.0, "digit_ratio": 0.0, "space_ratio": 0.0}

        total_chars = len(content)
        alpha_count = sum(1 for c in content if c.isalpha())
        digit_count = sum(1 for c in content if c.isdigit())
        space_count = sum(1 for c in content if c.isspace())

        return {
            "alpha_ratio": alpha_count / total_chars,
            "digit_ratio": digit_count / total_chars,
            "space_ratio": space_count / total_chars,
            "special_char_ratio": 1.0 - (alpha_count + digit_count + space_count) / total_chars
        }

    def _detect_language_simple(self, content: str) -> str:
        """Simple language detection based on common words"""
        if not content:
            return "unknown"

        # Convert to lowercase for matching
        content_lower = content.lower()

        # French indicators
        french_words = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'dans', 'pour',
                       'avec', 'sur', 'par', 'ce', 'que', 'qui', 'une', 'un', 'chapitre']
        french_score = sum(1 for word in french_words if word in content_lower)

        # English indicators
        english_words = ['the', 'and', 'is', 'in', 'for', 'with', 'on', 'by', 'that',
                        'which', 'a', 'an', 'this', 'chapter', 'section']
        english_score = sum(1 for word in english_words if word in content_lower)

        # German indicators
        german_words = ['der', 'die', 'das', 'und', 'ist', 'in', 'mit', 'auf', 'von',
                       'zu', 'ein', 'eine', 'kapitel']
        german_score = sum(1 for word in german_words if word in content_lower)

        # Spanish indicators
        spanish_words = ['el', 'la', 'los', 'las', 'de', 'del', 'y', 'es', 'en', 'con',
                        'por', 'para', 'que', 'un', 'una', 'capitulo']
        spanish_score = sum(1 for word in spanish_words if word in content_lower)

        # Determine language based on highest score
        scores = {
            'french': french_score,
            'english': english_score,
            'german': german_score,
            'spanish': spanish_score
        }

        max_score = max(scores.values())
        if max_score == 0:
            return "unknown"

        detected = max(scores, key=scores.get)
        return detected

    def get_document_stats(self, filepath: str) -> Dict[str, Any]:
        """Get comprehensive document statistics"""
        if not os.path.exists(filepath):
            return {"error": f"File not found: {filepath}"}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                return {"error": f"Could not read file: {str(e)}"}

        file_metadata = self.extract_from_filepath(filepath)
        content_metadata = self.extract_from_content(content)

        return {**file_metadata, **content_metadata}

    def validate_document_type(self, filepath: str) -> bool:
        """Check if document type is supported"""
        path = Path(filepath)
        return path.suffix.lower() in self.supported_extensions
