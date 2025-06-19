# src/rag_system/document_manager.py
import time
from typing import List, Optional, Dict, Any
from src.vector_stores.base_vector_store import BaseVectorStoreManager
from src.document_management import DocumentSelector


class DocumentManager:
    """
    Manages document lifecycle, selection, and metadata operations
    """

    def __init__(self, vector_store_manager: BaseVectorStoreManager,
                 document_selector: DocumentSelector):
        self.vector_store_manager = vector_store_manager
        self.document_selector = document_selector

    def finalize_document_processing(self, filename: str) -> None:
        print(f"🔄 Finalizing document processing for: {filename}")

        time.sleep(1)

        available_docs = self.get_available_documents()
        print(f"📚 Available documents after processing: {available_docs}")

        if filename not in available_docs:
            print(f"⚠️ Document {filename} not yet available, waiting...")
            time.sleep(2)
            available_docs = self.get_available_documents()
            print(f"📚 Available documents after wait: {available_docs}")

        if filename in available_docs:
            self.set_selected_document(filename)
            print(f"📖 Selected document: {filename}")
        else:
            print(f"⚠️ Could not select document {filename} - not found in available docs")

    def delete_document(self, document_filename: str) -> bool:
        print(f"🗑️ Deleting document: {document_filename}")

        available_docs = self.get_available_documents()
        if document_filename not in available_docs:
            print(f"❌ Document not found: {document_filename}")
            return False

        if self.get_selected_document() == document_filename:
            self.clear_selected_document()

        success = self.vector_store_manager.delete_document(document_filename)

        if success:
            print(f"🔄 Forcing refresh of document list...")

            remaining_docs = self.get_available_documents()
            print(f"📋 Documents after deletion: {remaining_docs}")

            if remaining_docs:
                print(f"✅ Document deleted successfully. {len(remaining_docs)} documents remaining.")
            else:
                print(f"✅ Document deleted. Knowledge base is now empty.")

            if document_filename not in remaining_docs:
                self.document_selector.persistence.clear_selection()

        else:
            print(f"❌ Failed to delete document: {document_filename}")

        return success

    def get_document_info(self, document_filename: str) -> Optional[Dict[str, Any]]:
        try:
            available_docs = self.get_available_documents()
            if document_filename not in available_docs:
                return None

            chunk_count = self.vector_store_manager.get_document_chunk_count(document_filename)

            # Get metadata for this document
            all_metadata = self.vector_store_manager.get_all_metadata()
            doc_metadata = [m for m in all_metadata if m.get('source_filename') == document_filename]

            # Calculate stats
            chapters = set()
            sections = set()
            total_words = 0

            for meta in doc_metadata:
                if meta.get('chapter_number'):
                    chapters.add(meta['chapter_number'])
                if meta.get('section_number'):
                    sections.add(meta['section_number'])
                total_words += meta.get('word_count', 0)

            return {
                "filename": document_filename,
                "chunk_count": chunk_count,
                "total_words": total_words,
                "chapters": sorted(list(chapters)),
                "sections": sorted(list(sections)),
                "document_type": doc_metadata[0].get('document_type', 'unknown') if doc_metadata else 'unknown'
            }

        except Exception as e:
            print(f"⚠️ Error getting document info for {document_filename}: {str(e)}")
            return None

    def get_available_documents(self) -> List[str]:
        return self.document_selector.get_available_documents()

    def set_selected_document(self, filename: str) -> None:
        self.document_selector.set_selected_document(filename)

    def clear_selected_document(self) -> None:
        self.document_selector.clear_selected_document()

    def get_selected_document(self) -> Optional[str]:
        return self.document_selector.get_selected_document()

    def get_document_stats(self) -> Dict[str, Any]:
        return self.document_selector.get_document_stats()
