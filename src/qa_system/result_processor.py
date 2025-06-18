# src/qa_system/result_processor.py
from typing import List, Dict, Any
from langchain.schema import Document


class ResultProcessor:
    """
    Process and format QA results, including metadata extraction and debugging
    """

    def __init__(self, enable_debug: bool = True):
        self.enable_debug = enable_debug
        self.metadata_keys_to_show = [
            'chapter_number', 'section_number', 'chapter_title',
            'source_filename', 'chunk_index'
        ]

    def process_qa_result(self, result: Dict[str, Any], enhanced_query: str) -> Dict[str, Any]:
        """
        Process QA chain result and add metadata information

        Args:
            result: Raw result from QA chain
            enhanced_query: The enhanced query that was used

        Returns:
            Processed result with additional metadata
        """
        if self.enable_debug:
            self._debug_print_retrieved_documents(result.get("source_documents", []))

        # Add query information to result
        processed_result = {
            **result,
            "enhanced_query": enhanced_query,
            "metadata_summary": self._extract_metadata_summary(result.get("source_documents", []))
        }

        return processed_result

    def filter_chapter_specific_documents(self, result: Dict[str, Any],
                                        chapter_filter: Dict[str, str]) -> Dict[str, Any]:
        """
        Filter result documents to ensure they match the requested chapter

        Args:
            result: QA chain result
            chapter_filter: Chapter/section filter criteria

        Returns:
            Result with filtered documents
        """
        source_documents = result.get("source_documents", [])

        filtered_docs = []
        for doc in source_documents:
            if self._document_matches_chapter_filter(doc, chapter_filter):
                filtered_docs.append(doc)

        if filtered_docs:
            result["source_documents"] = filtered_docs
            print(f"📊 Found {len(filtered_docs)} chapter-specific documents")
        else:
            print("⚠️ No chapter-specific documents found, using general results")

        return result

    def _document_matches_chapter_filter(self, doc: Document,
                                       chapter_filter: Dict[str, str]) -> bool:
        """
        Check if a document matches the chapter filter criteria

        Args:
            doc: Document to check
            chapter_filter: Filter criteria

        Returns:
            True if document matches any filter criteria
        """
        for key, value in chapter_filter.items():
            if doc.metadata.get(key) == value:
                return True
        return False

    def _extract_metadata_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Extract summary metadata from retrieved documents

        Args:
            documents: List of retrieved documents

        Returns:
            Dictionary with metadata summary
        """
        if not documents:
            return {}

        # Count documents by source
        sources = {}
        chapters = set()
        sections = set()

        for doc in documents:
            metadata = doc.metadata

            # Count by source filename
            source = metadata.get('source_filename', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            # Collect chapters and sections
            if metadata.get('chapter_number'):
                chapters.add(metadata['chapter_number'])
            if metadata.get('section_number'):
                sections.add(metadata['section_number'])

        return {
            "total_documents": len(documents),
            "sources": sources,
            "chapters": sorted(list(chapters)),
            "sections": sorted(list(sections))
        }

    def _debug_print_retrieved_documents(self, documents: List[Document]) -> None:
        """
        Print debug information about retrieved documents

        Args:
            documents: List of retrieved documents
        """
        if not self.enable_debug:
            return

        print("🔍 DEBUG: Retrieved documents metadata:")
        for i, doc in enumerate(documents):
            metadata_summary = {
                k: v for k, v in doc.metadata.items()
                if k in self.metadata_keys_to_show
            }
            print(f"   Doc {i+1}: {metadata_summary}")

    def format_final_output(self, result: Dict[str, Any]) -> None:
        """
        Print formatted final output

        Args:
            result: Processed QA result
        """
        answer = result.get('result', 'No answer available')
        source_count = len(result.get('source_documents', []))

        print(f"\n💡 Answer: {answer}")
        print(f"\n📚 Sources used: {source_count} chunks")

        if self.enable_debug and 'metadata_summary' in result:
            summary = result['metadata_summary']
            if summary.get('chapters'):
                print(f"📖 Chapters referenced: {', '.join(summary['chapters'])}")
            if summary.get('sources'):
                for source, count in summary['sources'].items():
                    print(f"📄 {source}: {count} chunks")
