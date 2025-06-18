# src/qa_system/query_enhancer.py
import re
from typing import Optional, List, Dict, Any


class QueryEnhancer:
    """
    Enhance user queries with context and conversation history
    """

    def __init__(self):
        self.chapter_patterns = [
            r'chapitre\s+(\d+|[ivxlc]+)',
            r'chapter\s+(\d+|[ivxlc]+)',
            r'section\s+(\d+|[ivxlc]+)',
            r'partie\s+(\d+|[ivxlc]+)',
            r'(\d+)\.(\d+)',
        ]

        self.roman_to_arabic = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
            'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15',
            'xvi': '16', 'xvii': '17', 'xviii': '18', 'xix': '19', 'xx': '20'
        }

    def build_context_from_history(self, question: str, chat_history: Optional[List[Dict]]) -> str:
        """
        Enhance a question with conversation context

        Args:
            question: The current question
            chat_history: Previous conversation messages

        Returns:
            Enhanced query string with conversation context
        """
        if not chat_history or len(chat_history) == 0:
            return question

        context_messages = []
        # Use last 6 messages for context (3 exchanges)
        for msg in chat_history[-6:]:
            role = "Human" if msg["role"] == "user" else "Assistant"
            context_messages.append(f"{role}: {msg['content']}")

        conversation_context = "\n".join(context_messages)
        enhanced_query = f"""Previous conversation:
{conversation_context}

Current question: {question}

Please answer the current question considering the conversation context above."""

        print("🧠 Using conversation context...")
        return enhanced_query

    def extract_chapter_filter(self, question: str) -> Optional[Dict[str, str]]:
        """
        Extract chapter/section information from user question

        Args:
            question: The user's question

        Returns:
            Dictionary with chapter/section filters or None
        """
        question_lower = question.lower()

        for pattern in self.chapter_patterns:
            match = re.search(pattern, question_lower)
            if match:
                groups = match.groups()

                # Handle section numbering like "1.2"
                if len(groups) == 2 and groups[0] and groups[1]:
                    return {
                        "section_number": groups[0],
                        "subsection_number": groups[1]
                    }

                # Handle single chapter/section numbers
                elif groups and len(groups) > 0 and groups[0]:
                    chapter_num = self._normalize_chapter_number(groups[0])
                    if chapter_num:
                        if 'chapitre' in pattern or 'chapter' in pattern:
                            return {"chapter_number": chapter_num}
                        else:
                            return {"section_number": chapter_num}

        return None

    def _normalize_chapter_number(self, chapter_str: str) -> str:
        """
        Convert roman numerals to arabic numbers if needed

        Args:
            chapter_str: Chapter number as string (could be roman or arabic)

        Returns:
            Normalized chapter number
        """
        if not chapter_str:
            return ""

        chapter_lower = chapter_str.lower().strip()

        # Convert roman to arabic if found
        if chapter_lower in self.roman_to_arabic:
            return self.roman_to_arabic[chapter_lower]

        return chapter_str.strip()
