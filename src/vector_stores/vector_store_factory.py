# src/vector_stores/vector_store_factory.py
import os
from typing import Union
from .chroma_vector_store import ChromaVectorStoreManager
from .qdrant_vector_store import QdrantVectorStoreManager


class VectorStoreFactory:

    @staticmethod
    def create_vector_store_manager(embeddings) -> Union[ChromaVectorStoreManager, QdrantVectorStoreManager]:
        vector_store_type = os.getenv("VECTOR_STORE_TYPE", "chroma").lower()

        if vector_store_type == "qdrant":
            return QdrantVectorStoreManager(embeddings)
        elif vector_store_type == "chroma":
            persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
            return ChromaVectorStoreManager(embeddings, persist_directory)
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")

    @staticmethod
    def get_supported_types():
        return ["chroma", "qdrant"]
