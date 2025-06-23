# src/document_management/agentic_document_processor.py
from typing import List, Dict, Any, Optional
from langchain.schema import Document
import concurrent.futures
from .agentic_chunker import AgenticChunker, ContextAwareChunker, AdaptiveAgenticChunker
from .document_processor import DocumentProcessor

class AgenticDocumentProcessor(DocumentProcessor):

    def __init__(self, embeddings, chunk_size: int = 2000, chunk_overlap: int = 200,
                 chunk_strategy: str = "agentic_basic", max_workers: int = 4):

        self.embeddings = embeddings
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_strategy = chunk_strategy
        self.max_workers = max_workers

        self._initialize_agentic_chunkers()

    def _initialize_agentic_chunkers(self):
        self.agentic_chunker = AgenticChunker(max_chunk_size=self.chunk_size)
        self.context_aware_chunker = ContextAwareChunker(max_chunk_size=self.chunk_size)
        self.adaptive_chunker = AdaptiveAgenticChunker()

    def process_documents_agentic(self, documents: List[Document]) -> List[Document]:
        if self.chunk_strategy == "agentic_basic":
            return self._process_with_basic_agentic(documents)
        elif self.chunk_strategy == "agentic_context":
            return self._process_with_context_aware(documents)
        elif self.chunk_strategy == "agentic_adaptive":
            return self._process_with_adaptive(documents)
        else:
            return super().process_documents(documents)

    def _process_with_basic_agentic(self, documents: List[Document]) -> List[Document]:
        all_chunks = []

        for doc in documents:
            print(f"🤖 Agentic chunking: {doc.metadata.get('source_filename', 'Unknown')}")

            chunks = self.agentic_chunker.chunk_document(
                doc.page_content,
                doc.metadata
            )

            enhanced_chunks = self._enhance_chunk_metadata(chunks)
            all_chunks.extend(enhanced_chunks)

        print(f"📊 Generated {len(all_chunks)} agentic chunks")
        return all_chunks

    def _process_with_context_aware(self, documents: List[Document]) -> List[Document]:
        all_chunks = []
        previous_chunks = []

        for doc in documents:
            print(f"🧠 Context-aware chunking: {doc.metadata.get('source_filename', 'Unknown')}")

            chunks = self.context_aware_chunker.chunk_document_with_context(
                doc.page_content,
                doc.metadata,
                previous_chunks
            )

            enhanced_chunks = self._enhance_chunk_metadata(chunks)
            all_chunks.extend(enhanced_chunks)
            previous_chunks = enhanced_chunks[-3:]  # Keep last 3 for context

        print(f"📊 Generated {len(all_chunks)} context-aware chunks")
        return all_chunks

    def _process_with_adaptive(self, documents: List[Document]) -> List[Document]:
        all_chunks = []

        for doc in documents:
            print(f"🎯 Adaptive chunking: {doc.metadata.get('source_filename', 'Unknown')}")

            feedback_scores = self._get_historical_feedback(doc.metadata)

            chunks = self.adaptive_chunker.chunk_with_learning(
                doc.page_content,
                doc.metadata,
                feedback_scores
            )

            enhanced_chunks = self._enhance_chunk_metadata(chunks)
            all_chunks.extend(enhanced_chunks)

        print(f"📊 Generated {len(all_chunks)} adaptive chunks")
        return all_chunks

    def _enhance_chunk_metadata(self, chunks: List[Document]) -> List[Document]:
        enhanced_chunks = []

        for chunk in chunks:
            metadata = chunk.metadata.copy()

            metadata.update({
                "word_count": len(chunk.page_content.split()),
                "char_count": len(chunk.page_content),
                "processing_method": "agentic",
                "semantic_coherence": self._calculate_coherence_score(chunk.page_content)
            })

            enhanced_chunk = Document(
                page_content=chunk.page_content,
                metadata=metadata
            )
            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    def _calculate_coherence_score(self, text: str) -> float:
        sentences = text.split('.')
        if len(sentences) < 2:
            return 1.0

        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        length_variance = sum((l - avg_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)

        coherence = max(0.0, 1.0 - (length_variance / (avg_length ** 2)))
        return min(1.0, coherence)

    def _get_historical_feedback(self, metadata: Dict[str, Any]) -> Optional[List[float]]:
        doc_name = metadata.get('source_filename', '')

        feedback_store = getattr(self, '_feedback_store', {})
        return feedback_store.get(doc_name, None)

    def update_feedback(self, document_name: str, chunk_scores: List[float]):
        if not hasattr(self, '_feedback_store'):
            self._feedback_store = {}
        self._feedback_store[document_name] = chunk_scores

class HybridAgenticProcessor(AgenticDocumentProcessor):

    def __init__(self, embeddings, chunk_size: int = 2000, chunk_overlap: int = 200,
                 chunk_strategy: str = "hybrid_agentic", max_workers: int = 4):
        super().__init__(embeddings, chunk_size, chunk_overlap, chunk_strategy, max_workers)

        from .document_processor import DocumentProcessor
        self.traditional_processor = DocumentProcessor(
            embeddings, chunk_size, chunk_overlap, "semantic", max_workers
        )

    def process_documents_hybrid(self, documents: List[Document]) -> List[Document]:
        agentic_chunks = []
        traditional_chunks = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_agentic = executor.submit(self._process_with_basic_agentic, documents)
            future_traditional = executor.submit(self.traditional_processor.process_documents, documents)

            agentic_chunks = future_agentic.result()
            traditional_chunks = future_traditional.result()

        merged_chunks = self._merge_chunking_strategies(agentic_chunks, traditional_chunks)
        return merged_chunks

    def _merge_chunking_strategies(self, agentic_chunks: List[Document],
                                 traditional_chunks: List[Document]) -> List[Document]:
        merged = []

        for i, (agent_chunk, trad_chunk) in enumerate(zip(agentic_chunks, traditional_chunks)):
            if self._evaluate_chunk_quality(agent_chunk) > self._evaluate_chunk_quality(trad_chunk):
                agent_chunk.metadata["chunking_winner"] = "agentic"
                merged.append(agent_chunk)
            else:
                trad_chunk.metadata["chunking_winner"] = "traditional"
                merged.append(trad_chunk)

        if len(agentic_chunks) != len(traditional_chunks):
            longer_list = agentic_chunks if len(agentic_chunks) > len(traditional_chunks) else traditional_chunks
            merged.extend(longer_list[min(len(agentic_chunks), len(traditional_chunks)):])

        return merged

    def _evaluate_chunk_quality(self, chunk: Document) -> float:
        text = chunk.page_content

        length_score = min(1.0, len(text) / self.chunk_size)

        sentences = text.split('.')
        sentence_score = min(1.0, len([s for s in sentences if len(s.strip()) > 10]) / 5)

        coherence_score = chunk.metadata.get("semantic_coherence", 0.5)

        return (length_score * 0.3 + sentence_score * 0.3 + coherence_score * 0.4)
