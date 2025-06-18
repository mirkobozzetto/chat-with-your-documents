# src/document_processor.py
import os
import re
import concurrent.futures
from typing import List, Callable, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.schema import Document


class DocumentProcessor:

    def __init__(self, embeddings, chunk_strategy: str, chunk_size: int, chunk_overlap: int):
        self.embeddings = embeddings
        self.chunk_strategy = chunk_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_workers = 4

        if chunk_strategy == "semantic":
            print("📚 Using Semantic Chunking Strategy")
            self.text_splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95
            )
        else:
            print("📚 Using Recursive Character Chunking")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )

    def load_document(self, file_path: str, progress_callback: Optional[Callable] = None) -> List[Document]:
        print(f"📄 Loading document: {file_path}")

        if progress_callback:
            progress_callback(0.1, "Loading document...")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        file_ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name

        loaders = {
            '.pdf': lambda: PyPDFLoader(file_path),
            '.docx': lambda: UnstructuredWordDocumentLoader(file_path),
            '.txt': lambda: TextLoader(file_path, encoding='utf-8'),
            '.md': lambda: TextLoader(file_path, encoding='utf-8')
        }

        if file_ext not in loaders:
            raise ValueError(f"Unsupported format: {file_ext}")

        loader = loaders[file_ext]()

        if progress_callback:
            progress_callback(0.3, "Extracting text...")

        documents = loader.load()

        for doc in documents:
            doc.metadata["source_filename"] = filename
            doc.metadata["document_type"] = file_ext[1:]

            chapter_info = self._extract_chapter_info(doc.page_content)
            if chapter_info:
                doc.metadata.update(chapter_info)

        if progress_callback:
            progress_callback(0.5, f"Loaded {len(documents)} sections")

        print(f"✅ Loaded {len(documents)} sections from document")
        return documents

    def chunk_documents(self, documents: List[Document], progress_callback: Optional[Callable] = None) -> List[Document]:
        print(f"🔄 Chunking documents with {self.chunk_strategy} strategy...")

        if progress_callback:
            progress_callback(0.6, "Chunking documents...")

        if self.chunk_strategy == "semantic":
            # Create a mapping of text positions to metadata for semantic chunking
            text_sections = []
            section_metadata = []
            
            for doc in documents:
                text_sections.append(doc.page_content)
                section_metadata.append(doc.metadata)
            
            combined_text = "\n\n".join(text_sections)
            chunks = self.text_splitter.create_documents([combined_text])

            filename = documents[0].metadata.get("source_filename", "unknown")
            doc_type = documents[0].metadata.get("document_type", "unknown")

            for i, chunk in enumerate(chunks):
                chunk.metadata["source_filename"] = filename
                chunk.metadata["document_type"] = doc_type

                # Extract chapter info for each chunk
                chapter_info = self._extract_chapter_info(chunk.page_content)
                if chapter_info:
                    chunk.metadata.update(chapter_info)
                else:
                    # If no chapter info found, try to inherit from nearby content
                    inherited_metadata = self._inherit_metadata_from_nearby_content(
                        chunk.page_content, text_sections, section_metadata
                    )
                    if inherited_metadata:
                        chunk.metadata.update(inherited_metadata)

                # Add chunk index for better tracking
                chunk.metadata["chunk_index"] = i
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                chunk_futures = []

                batch_size = max(1, len(documents) // self.max_workers)
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    future = executor.submit(self.text_splitter.split_documents, batch)
                    chunk_futures.append(future)

                chunks = []
                for future in concurrent.futures.as_completed(chunk_futures):
                    batch_chunks = future.result()
                    for i, chunk in enumerate(batch_chunks):
                        # Extract chapter info for each chunk
                        chapter_info = self._extract_chapter_info(chunk.page_content)
                        if chapter_info:
                            chunk.metadata.update(chapter_info)
                        # Add global chunk index
                        chunk.metadata["chunk_index"] = len(chunks) + i
                    chunks.extend(batch_chunks)

        if progress_callback:
            progress_callback(0.8, f"Created {len(chunks)} chunks")

        print(f"✅ Created {len(chunks)} optimized chunks")
        return chunks

    def process_document_pipeline(self, file_path: str, progress_callback: Optional[Callable] = None) -> List[Document]:
        if progress_callback:
            progress_callback(0.05, "Starting processing...")

        documents = self.load_document(file_path, progress_callback)
        chunks = self.chunk_documents(documents, progress_callback)

        if progress_callback:
            progress_callback(0.9, "Processing complete!")

        return chunks

    def estimate_processing_time(self, file_size_mb: float) -> str:
        if file_size_mb < 1:
            return "~10 seconds"
        elif file_size_mb < 5:
            return "~30 seconds"
        elif file_size_mb < 20:
            return "~1-2 minutes"
        elif file_size_mb < 100:
            return "~3-5 minutes"
        else:
            return "~5-10 minutes"

    def _extract_chapter_info(self, text: str) -> Optional[dict]:
        """Extract chapter information from text content."""
        if not text or len(text.strip()) < 10:
            return None

        chapter_patterns = [
            # French patterns
            r'(?i)chapitre\s+(\d+|[ivxlc]+)(?:\s*[:\-\.]\s*(.+?))?(?=\n|\r|$)',
            r'(?i)chapter\s+(\d+|[ivxlc]+)(?:\s*[:\-\.]\s*(.+?))?(?=\n|\r|$)',
            # Numbered sections
            r'^(\d+)\.(\d+)?\.?\s+(.+?)(?=\n|\r|$)',
            # Section headers
            r'(?i)^(section|partie)\s+(\d+|[ivxlc]+)(?:\s*[:\-\.]\s*(.+?))?(?=\n|\r|$)',
        ]

        lines = text.split('\n')[:5]  # Check first 5 lines

        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in chapter_patterns:
                match = re.search(pattern, line, re.MULTILINE)
                if match:
                    groups = match.groups()
                    chapter_info = {}

                    if 'chapitre' in pattern.lower() or 'chapter' in pattern.lower():
                        chapter_num = groups[0] if groups and len(groups) > 0 else None
                        if chapter_num:  # Check for None
                            chapter_info['chapter_number'] = self._normalize_chapter_number(chapter_num)
                        if len(groups) > 1 and groups[1]:
                            chapter_info['chapter_title'] = groups[1].strip()
                    elif pattern.startswith(r'^\d+'):
                        # Section numbering like "1.2 Title"
                        if groups and len(groups) > 0 and groups[0]:  # Check for None
                            chapter_info['section_number'] = groups[0]
                        if len(groups) > 1 and groups[1]:
                            chapter_info['subsection_number'] = groups[1]
                        if len(groups) > 2 and groups[2]:
                            chapter_info['section_title'] = groups[2].strip()
                    else:
                        # Section/Partie
                        section_num = groups[1] if len(groups) > 1 and groups[1] else (groups[0] if groups and len(groups) > 0 else None)
                        if section_num:  # Check for None
                            chapter_info['section_number'] = self._normalize_chapter_number(section_num)
                        if len(groups) > 2 and groups[2]:
                            chapter_info['section_title'] = groups[2].strip()

                    # Only return if we actually found some chapter info
                    if chapter_info:
                        return chapter_info

        return None

    def _normalize_chapter_number(self, chapter_str: str) -> str:
        """Normalize chapter numbers (convert roman to arabic if needed)."""
        if not chapter_str:  # Check for None or empty string
            return ""
            
        roman_to_arabic = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10',
            'xi': '11', 'xii': '12', 'xiii': '13', 'xiv': '14', 'xv': '15',
            'xvi': '16', 'xvii': '17', 'xviii': '18', 'xix': '19', 'xx': '20'
        }

        chapter_lower = chapter_str.lower().strip()
        if chapter_lower in roman_to_arabic:
            return roman_to_arabic[chapter_lower]

        return chapter_str.strip()
    
    def _inherit_metadata_from_nearby_content(self, chunk_text: str, original_sections: List[str], section_metadata: List[dict]) -> Optional[dict]:
        """Try to inherit chapter metadata from nearby content in the original document."""
        if not chunk_text or not original_sections:
            return None
            
        chunk_words = set(chunk_text.lower().split()[:20])  # First 20 words of chunk
        
        best_match_score = 0
        best_metadata = None
        
        for section_text, metadata in zip(original_sections, section_metadata):
            if not section_text or len(section_text.strip()) < 50:
                continue
                
            section_words = set(section_text.lower().split()[:50])  # First 50 words of section
            overlap = len(chunk_words.intersection(section_words))
            
            if overlap > best_match_score:
                best_match_score = overlap
                # Only inherit chapter-related metadata
                chapter_metadata = {}
                for key in ['chapter_number', 'chapter_title', 'section_number', 'subsection_number', 'section_title']:
                    if key in metadata:
                        chapter_metadata[key] = metadata[key]
                
                if chapter_metadata:
                    best_metadata = chapter_metadata
        
        return best_metadata if best_match_score > 2 else None
