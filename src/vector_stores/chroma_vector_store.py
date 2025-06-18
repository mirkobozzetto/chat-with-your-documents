# src/vector_stores/chroma_vector_store.py
import os
from typing import List, Optional, Callable
from langchain_chroma import Chroma
from langchain.schema import Document
from .base_vector_store import BaseVectorStoreManager


class ChromaVectorStoreManager(BaseVectorStoreManager):

    def __init__(self, embeddings, persist_directory: str):
        super().__init__(embeddings)
        self.persist_directory = persist_directory
        self.vector_store = self._load_existing_vector_store()

    def _load_existing_vector_store(self) -> Optional[Chroma]:
        try:
            if os.path.exists(self.persist_directory):
                vector_store = Chroma(
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                return vector_store
        except Exception as e:
            print(f"⚠️ Could not load existing vector store: {str(e)}")
        return None

    def has_documents(self) -> bool:
        try:
            if self.vector_store:
                collection = self.vector_store._collection
                return collection.count() > 0
        except:
            return False
        return False

    def create_vector_store(self, chunks: List[Document], progress_callback: Optional[Callable] = None) -> None:
        print("🗄️ Creating ChromaDB vector store...")

        if not self.vector_store:
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )

        batch_size = 50
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"📦 Processing batch {batch_num}/{total_batches}")

            self.vector_store.add_documents(batch)

            if progress_callback:
                progress = 0.9 + (batch_num / total_batches) * 0.1
                progress_callback(progress, f"Batch {batch_num}/{total_batches}")

        print(f"✅ ChromaDB vector store created with {len(chunks)} chunks")

    def get_vector_store(self) -> Optional[Chroma]:
        return self.vector_store

    def get_chunk_count(self) -> int:
        if not self.vector_store:
            return 0

        try:
            collection = self.vector_store._collection
            return collection.count()
        except:
            return 0

    def get_all_metadata(self) -> List[dict]:
        if not self.vector_store:
            return []

        try:
            collection = self.vector_store._collection
            return collection.get()["metadatas"]
        except Exception as e:
            print(f"⚠️ Error getting metadata: {str(e)}")
            return []

    def delete_document(self, document_filename: str) -> bool:
        """Delete all chunks for a specific document from ChromaDB"""
        if not self.vector_store:
            print(f"❌ No vector store available")
            return False

        try:
            collection = self.vector_store._collection

            # Get all documents with this filename
            results = collection.get(
                where={"source_filename": document_filename},
                include=["documents", "metadatas"]
            )

            if not results["ids"]:
                print(f"📭 No chunks found for document: {document_filename}")
                return True  # Nothing to delete is still success

            # Delete all chunks for this document
            collection.delete(ids=results["ids"])

            print(f"🗑️ Deleted {len(results['ids'])} chunks for document: {document_filename}")
            return True

        except Exception as e:
            print(f"❌ Error deleting document {document_filename}: {str(e)}")
            return False

    def get_document_chunk_count(self, document_filename: str) -> int:
        """Get number of chunks for a specific document"""
        if not self.vector_store:
            return 0

        try:
            collection = self.vector_store._collection
            results = collection.get(
                where={"source_filename": document_filename},
                include=[]
            )
            return len(results["ids"])
        except Exception as e:
            print(f"⚠️ Error counting chunks for {document_filename}: {str(e)}")
            return 0
