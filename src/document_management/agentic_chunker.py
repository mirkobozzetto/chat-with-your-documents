# src/document_management/agentic_chunker.py
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

class AgenticChunker:

    def __init__(self, llm_model: str = "gpt-4.1-2025-04-14", max_chunk_size: int = 2000):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.max_chunk_size = max_chunk_size

    def chunk_document(self, text: str, document_metadata: Dict[str, Any]) -> List[Document]:
        if len(text) <= self.max_chunk_size:
            return [Document(page_content=text, metadata=document_metadata)]

        semantic_boundaries = self._identify_semantic_boundaries(text)
        chunks = self._create_chunks_from_boundaries(text, semantic_boundaries, document_metadata)

        return chunks

    def _identify_semantic_boundaries(self, text: str) -> List[int]:
        prompt = ChatPromptTemplate.from_template("""
Analyze this text and identify optimal semantic boundaries for chunking.
Consider:
- Topic transitions
- Conceptual completeness
- Natural breakpoints (paragraphs, sections)
- Maintaining context within chunks

Text length: {text_length} characters
Max chunk size: {max_chunk_size}

Text:
{text}

Return JSON with boundary positions (character indices):
{{"boundaries": [position1, position2, ...]}}
""")

        response = self.llm.invoke(
            prompt.format_messages(
                text=text[:4000],  # Limit for LLM context
                text_length=len(text),
                max_chunk_size=self.max_chunk_size
            )
        )

        try:
            result = json.loads(response.content)
            boundaries = result.get("boundaries", [])
            return [0] + boundaries + [len(text)]
        except:
            return self._fallback_boundaries(text)

    def _fallback_boundaries(self, text: str) -> List[int]:
        boundaries = [0]
        paragraphs = text.split('\n\n')
        current_pos = 0

        for paragraph in paragraphs:
            current_pos += len(paragraph) + 2
            if current_pos - boundaries[-1] > self.max_chunk_size * 0.7:
                boundaries.append(current_pos)

        return boundaries + [len(text)]

    def _create_chunks_from_boundaries(self, text: str, boundaries: List[int],
                                     metadata: Dict[str, Any]) -> List[Document]:
        chunks = []

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_method": "agentic",
                    "chunk_start": start,
                    "chunk_end": end,
                    "chunk_size": len(chunk_text)
                })

                chunks.append(Document(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                ))

        return chunks

class ContextAwareChunker(AgenticChunker):

    def __init__(self, llm_model: str = "gpt-4.1-2025-04-14", max_chunk_size: int = 2000):
        super().__init__(llm_model, max_chunk_size)

    def chunk_document_with_context(self, text: str, document_metadata: Dict[str, Any],
                                   previous_chunks: List[Document] = None) -> List[Document]:

        context_info = self._extract_document_context(text, previous_chunks)
        enhanced_metadata = {**document_metadata, **context_info}

        return super().chunk_document(text, enhanced_metadata)

    def _extract_document_context(self, text: str, previous_chunks: List[Document] = None) -> Dict[str, Any]:
        prompt = ChatPromptTemplate.from_template("""
Analyze this document to extract structural and contextual information:

Document preview:
{text_preview}

Identify:
1. Document type and domain
2. Main topics/themes
3. Structural elements (chapters, sections, etc.)
4. Recommended chunking strategy

Return JSON:
{{
    "document_type": "academic|technical|creative|legal|medical",
    "domain": "string",
    "main_topics": ["topic1", "topic2"],
    "has_structure": boolean,
    "recommended_chunk_size": number,
    "chunking_priority": "semantic|structural|hybrid"
}}
""")

        response = self.llm.invoke(
            prompt.format_messages(text_preview=text[:2000])
        )

        try:
            return json.loads(response.content)
        except:
            return {
                "document_type": "unknown",
                "chunking_priority": "semantic"
            }

class AdaptiveAgenticChunker(ContextAwareChunker):

    def __init__(self, llm_model: str = "gpt-4.1-2025-04-14"):
        super().__init__(llm_model)
        self.chunk_history = []

    def chunk_with_learning(self, text: str, document_metadata: Dict[str, Any],
                           feedback_scores: Optional[List[float]] = None) -> List[Document]:

        if feedback_scores and self.chunk_history:
            self._update_chunking_strategy(feedback_scores)

        context_info = self._extract_document_context(text)
        adapted_strategy = self._adapt_strategy_from_history(context_info)

        chunks = self._chunk_with_strategy(text, document_metadata, adapted_strategy)

        self.chunk_history.append({
            "context": context_info,
            "strategy": adapted_strategy,
            "chunk_count": len(chunks),
            "avg_chunk_size": sum(len(c.page_content) for c in chunks) / len(chunks)
        })

        return chunks

    def _adapt_strategy_from_history(self, context_info: Dict[str, Any]) -> Dict[str, Any]:
        similar_docs = [
            h for h in self.chunk_history
            if h["context"].get("document_type") == context_info.get("document_type")
        ]

        if similar_docs:
            avg_chunk_size = sum(h["avg_chunk_size"] for h in similar_docs) / len(similar_docs)
            return {
                "target_chunk_size": int(avg_chunk_size),
                "overlap_ratio": 0.15,
                "boundary_detection": "enhanced"
            }

        return {
            "target_chunk_size": self.max_chunk_size,
            "overlap_ratio": 0.1,
            "boundary_detection": "standard"
        }

    def _chunk_with_strategy(self, text: str, metadata: Dict[str, Any],
                           strategy: Dict[str, Any]) -> List[Document]:

        self.max_chunk_size = strategy["target_chunk_size"]

        if strategy["boundary_detection"] == "enhanced":
            return self._enhanced_boundary_detection(text, metadata)
        else:
            return self.chunk_document(text, metadata)

    def _enhanced_boundary_detection(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        prompt = ChatPromptTemplate.from_template("""
Perform advanced semantic boundary detection for this text.

Consider:
- Conceptual coherence within chunks
- Natural topic transitions
- Discourse markers and connectives
- Paragraph and sentence boundaries
- Optimal information density

Text: {text}
Target chunk size: {target_size}

Provide detailed boundary analysis:
{{
    "boundaries": [
        {{"position": number, "confidence": float, "reason": "string"}},
        ...
    ]
}}
""")

        response = self.llm.invoke(
            prompt.format_messages(
                text=text[:3000],
                target_size=self.max_chunk_size
            )
        )

        try:
            result = json.loads(response.content)
            high_confidence_boundaries = [
                b["position"] for b in result["boundaries"]
                if b.get("confidence", 0) > 0.7
            ]
            return self._create_chunks_from_boundaries(text, high_confidence_boundaries, metadata)
        except:
            return self.chunk_document(text, metadata)

    def _update_chunking_strategy(self, feedback_scores: List[float]):
        avg_score = sum(feedback_scores) / len(feedback_scores)

        if avg_score < 0.6:  # Poor performance
            if hasattr(self, 'last_strategy'):
                if self.last_strategy.get("boundary_detection") == "standard":
                    self.last_strategy["boundary_detection"] = "enhanced"
                self.last_strategy["target_chunk_size"] = int(self.last_strategy["target_chunk_size"] * 0.8)
