# src/document_selector.py
from typing import List, Optional
from src.vector_store_manager import VectorStoreManager


class DocumentSelector:

    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.selected_document: Optional[str] = None

    def get_available_documents(self) -> List[str]:
        all_metadata = self.vector_store_manager.get_all_metadata()

        if not all_metadata:
            return []

        try:
            filenames = set()
            for metadata in all_metadata:
                if "source_filename" in metadata:
                    filenames.add(metadata["source_filename"])

            return sorted(list(filenames))
        except Exception as e:
            print(f"⚠️ Error getting available documents: {str(e)}")
            return []

    def set_selected_document(self, filename: str) -> None:
        available_docs = self.get_available_documents()
        if filename in available_docs:
            self.selected_document = filename
            print(f"📖 Selected document: {filename}")
        else:
            raise ValueError(f"Document '{filename}' not found in knowledge base")

    def clear_selected_document(self) -> None:
        self.selected_document = None
        print("🌐 Cleared document selection - querying all documents")

    def get_selected_document(self) -> Optional[str]:
        return self.selected_document

    def get_document_filter(self) -> Optional[dict]:
        if self.selected_document:
            return {"source_filename": self.selected_document}
        return None

    def has_selected_document(self) -> bool:
        return self.selected_document is not None

    def get_document_stats(self) -> dict:
        available_docs = self.get_available_documents()

        return {
            "total_documents": len(available_docs),
            "available_documents": available_docs,
            "selected_document": self.selected_document,
            "has_selection": self.has_selected_document()
        }
