# src/metadata/extractors/chapter_extractor.py
import re
from typing import Optional, Dict, Any, List, Tuple
from ..models.document_metadata import ChapterMetadata, SectionMetadata


class ChapterExtractor:
    """Extract chapter and section information from document content"""

    def __init__(self):
        # Chapter patterns - order matters for precedence
        self.chapter_patterns = [
            # French patterns
            (r'(?:chapitre|chap\.?)\s+([ivxlc]+|[0-9]+)(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),
            (r'([ivxlc]+|[0-9]+)\s*(?:er|ème|eme)?\s*chapitre(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),

            # English patterns
            (r'chapter\s+([ivxlc]+|[0-9]+)(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),
            (r'ch\.?\s*([0-9]+)(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),

            # Generic numbered patterns
            (r'^([0-9]+)\.\s*([A-Z][^.]+?)(?:\n|$)', re.MULTILINE),
        ]

        # Section patterns
        self.section_patterns = [
            # Numbered sections like "1.1", "2.3.1"
            (r'(?:section\s+)?([0-9]+(?:\.[0-9]+)+)(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),
            (r'^([0-9]+\.[0-9]+(?:\.[0-9]+)*)\s+([A-Z][^.\n]+?)(?:\n|$)', re.MULTILINE),

            # Named sections
            (r'(?:section|partie)\s+([0-9]+|[ivxlc]+)(?:\s*[:\-–—]\s*(.+?))?(?:\n|$)', re.IGNORECASE),

            # Subsection patterns
            (r'([0-9]+)\.([0-9]+)(?:\.([0-9]+))?\s+(.+?)(?:\n|$)', re.MULTILINE),
        ]

        # Roman numeral mapping
        self.roman_to_arabic = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
            'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15',
            'xvi': '16', 'xvii': '17', 'xviii': '18', 'xix': '19', 'xx': '20'
        }

    def extract_chapter_info(self, content: str) -> Optional[ChapterMetadata]:
        """Extract chapter information from content"""
        # Clean content for better matching
        clean_content = self._clean_content_for_extraction(content)

        for pattern, flags in self.chapter_patterns:
            match = re.search(pattern, clean_content, flags)
            if match:
                raw_number = match.group(1).strip()
                title = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None

                # Clean title
                if title:
                    title = self._clean_title(title)
                    if not title or len(title) < 3:  # Skip very short titles
                        title = None

                # Normalize chapter number
                normalized_number = self._normalize_chapter_number(raw_number)

                return ChapterMetadata(
                    number=normalized_number,
                    title=title,
                    raw_number=raw_number
                )

        return None

    def extract_section_info(self, content: str) -> Optional[SectionMetadata]:
        """Extract section information from content"""
        clean_content = self._clean_content_for_extraction(content)

        for pattern, flags in self.section_patterns:
            match = re.search(pattern, clean_content, flags)
            if match:
                if len(match.groups()) >= 2:
                    section_num = match.group(1).strip()
                    title = match.group(2).strip() if match.group(2) else None

                    # Handle subsections (e.g., "1.2.3")
                    subsection = None
                    level = 1

                    if '.' in section_num:
                        parts = section_num.split('.')
                        level = len(parts)
                        if level > 2:
                            subsection = '.'.join(parts[2:])
                        section_num = '.'.join(parts[:2])

                    # Clean title
                    if title:
                        title = self._clean_title(title)
                        if not title or len(title) < 3:
                            title = None

                    return SectionMetadata(
                        number=section_num,
                        subsection=subsection,
                        title=title,
                        level=level
                    )

        return None

    def extract_all_metadata(self, content: str) -> Dict[str, Any]:
        """Extract both chapter and section metadata"""
        result = {}

        chapter = self.extract_chapter_info(content)
        if chapter:
            result.update({
                "chapter_number": chapter.number,
                "chapter_title": chapter.title,
                "chapter_raw_number": chapter.raw_number
            })

        section = self.extract_section_info(content)
        if section:
            result.update({
                "section_number": section.number,
                "subsection_number": section.subsection,
                "section_title": section.title,
                "section_level": section.level
            })

        return result

    def find_structural_elements(self, content: str) -> List[Dict[str, Any]]:
        """Find all structural elements (chapters, sections) in content"""
        elements = []

        # Find all chapters
        for pattern, flags in self.chapter_patterns:
            for match in re.finditer(pattern, content, flags):
                raw_number = match.group(1).strip()
                title = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None

                elements.append({
                    "type": "chapter",
                    "number": self._normalize_chapter_number(raw_number),
                    "raw_number": raw_number,
                    "title": self._clean_title(title) if title else None,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "matched_text": match.group(0)
                })

        # Find all sections
        for pattern, flags in self.section_patterns:
            for match in re.finditer(pattern, content, flags):
                if len(match.groups()) >= 2:
                    section_num = match.group(1).strip()
                    title = match.group(2).strip() if match.group(2) else None

                    elements.append({
                        "type": "section",
                        "number": section_num,
                        "title": self._clean_title(title) if title else None,
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                        "matched_text": match.group(0)
                    })

        # Sort by position in document
        elements.sort(key=lambda x: x["start_pos"])
        return elements

    def _clean_content_for_extraction(self, content: str) -> str:
        """Clean content to improve extraction accuracy"""
        # Take first portion of content where structure is most likely
        content = content[:2000]  # First 2000 chars usually contain structure

        # Remove extra whitespace but preserve line structure
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _clean_title(self, title: str) -> Optional[str]:
        """Clean extracted titles"""
        if not title:
            return None

        # Remove common artifacts
        title = re.sub(r'[^\w\s\-–—\'\"().,]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        title = title.strip()

        # Remove trailing punctuation except important ones
        title = re.sub(r'[.,:;]+$', '', title)

        # Skip if too short or looks like garbage
        if len(title) < 3 or len(title) > 200:
            return None

        # Skip if mostly numbers or special chars
        alpha_ratio = sum(c.isalpha() for c in title) / len(title)
        if alpha_ratio < 0.3:
            return None

        return title

    def _normalize_chapter_number(self, raw_number: str) -> str:
        """Normalize chapter numbers to consistent format"""
        if not raw_number:
            return ""

        raw_lower = raw_number.lower().strip()

        # Convert roman numerals
        if raw_lower in self.roman_to_arabic:
            return self.roman_to_arabic[raw_lower]

        # Extract digits from mixed content
        digits = re.findall(r'\d+', raw_number)
        if digits:
            return digits[0]

        return raw_number.strip()

    def inherit_metadata_from_sections(self, chunk_content: str,
                                     document_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Inherit metadata from document sections based on content similarity"""
        if not document_sections:
            return {}

        # Get first 20 words of chunk for matching
        chunk_words = set(chunk_content.lower().split()[:20])

        best_match = None
        best_score = 0

        for section in document_sections:
            if "matched_text" in section:
                # Get first 50 words of section for matching
                section_words = set(section["matched_text"].lower().split()[:50])

                # Calculate word overlap
                overlap = len(chunk_words.intersection(section_words))
                if overlap > best_score and overlap > 2:  # Minimum 3 word overlap
                    best_score = overlap
                    best_match = section

        if best_match:
            inherited = {}
            if best_match["type"] == "chapter":
                inherited.update({
                    "chapter_number": best_match["number"],
                    "chapter_title": best_match.get("title"),
                    "chapter_raw_number": best_match.get("raw_number")
                })
            elif best_match["type"] == "section":
                inherited.update({
                    "section_number": best_match["number"],
                    "section_title": best_match.get("title")
                })

            if inherited:
                inherited["inherited_metadata"] = True
                return inherited

        return {}
