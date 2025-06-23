# src/rag_system/contextual_preprocessor.py
from typing import List
from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
import logging
from dataclasses import dataclass

@dataclass
class ContextualChunk:
    original_chunk: Document
    contextual_explanation: str
    enhanced_content: str

class ContextualPreprocessor:
    def __init__(self, llm: BaseLanguageModel, batch_size: int = 10):
        self.llm = llm
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        self.context_prompt = PromptTemplate(
            template="""<document>
{document_content}
</document>

Here is the chunk we want to situate within the document:
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the context and nothing else.""",
            input_variables=["document_content", "chunk_content"]
        )

    def process_chunks(self, chunks: List[Document], document_content: str) -> List[ContextualChunk]:
        contextual_chunks = []

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_results = self._process_batch(batch, document_content)
            contextual_chunks.extend(batch_results)

        return contextual_chunks

    def _process_batch(self, chunks: List[Document], document_content: str) -> List[ContextualChunk]:
        batch_results = []

        for chunk in chunks:
            try:
                context = self._generate_context(chunk, document_content)
                enhanced_content = f"{context}\n\n{chunk.page_content}"

                contextual_chunk = ContextualChunk(
                    original_chunk=chunk,
                    contextual_explanation=context,
                    enhanced_content=enhanced_content
                )
                batch_results.append(contextual_chunk)

            except Exception as e:
                self.logger.warning(f"Failed to generate context for chunk: {e}")
                fallback_chunk = ContextualChunk(
                    original_chunk=chunk,
                    contextual_explanation="",
                    enhanced_content=chunk.page_content
                )
                batch_results.append(fallback_chunk)

        return batch_results

    def _generate_context(self, chunk: Document, document_content: str) -> str:
        prompt = self.context_prompt.format(
            document_content=document_content[:8000],
            chunk_content=chunk.page_content
        )

        response = self.llm.invoke(prompt)
        return response.content.strip()

    def create_enhanced_documents(self, contextual_chunks: List[ContextualChunk]) -> List[Document]:
        enhanced_docs = []

        for ctx_chunk in contextual_chunks:
            enhanced_doc = Document(
                page_content=ctx_chunk.enhanced_content,
                metadata={
                    **ctx_chunk.original_chunk.metadata,
                    "contextual_explanation": ctx_chunk.contextual_explanation,
                    "is_contextual": True
                }
            )
            enhanced_docs.append(enhanced_doc)

        return enhanced_docs
