# src/vector_stores/vector_store_manager.py
import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain.schema import Document


class VectorStoreManager:

    def __init__(self, embeddings, persist_directory: str):
        self.embeddings = embeddings
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

    def create_vector_store(self, chunks: List[Document]) -> None:
        print("🗄️ Creating optimized vector store...")

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

        print(f"✅ Vector store created with {len(chunks)} chunks")

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
