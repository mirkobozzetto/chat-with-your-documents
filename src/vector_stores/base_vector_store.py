# src/vector_stores/base_vector_store.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Callable
from langchain.schema import Document


class BaseVectorStoreManager(ABC):

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vector_store = None

    @abstractmethod
    def has_documents(self) -> bool:
        pass

    @abstractmethod
    def create_vector_store(self, chunks: List[Document], progress_callback: Optional[Callable] = None) -> None:
        pass

    @abstractmethod
    def get_vector_store(self) -> Optional[Any]:
        pass

    @abstractmethod
    def get_chunk_count(self) -> int:
        pass

    @abstractmethod
    def get_all_metadata(self) -> List[dict]:
        pass

    @abstractmethod
    def _load_existing_vector_store(self) -> Optional[Any]:
        pass
