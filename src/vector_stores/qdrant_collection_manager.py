# src/vector_stores/qdrant_collection_manager.py
from typing import Set, Dict, Any
from qdrant_client.models import Distance, VectorParams
from .custom_qdrant_client import CustomQdrantClient
from .collection_name_manager import CollectionNameManager


class QdrantCollectionManager:
    """
    Manage Qdrant collections lifecycle
    (create, delete, list, check existence)
    """

    def __init__(self, client: CustomQdrantClient):
        self.client = client
        self.name_manager = CollectionNameManager()

    def ensure_document_collection_exists(self, document_filename: str, vector_size: int = 3072) -> str:
        """
        Ensure a collection exists for the given document

        Args:
            document_filename: Name of the document
            vector_size: Size of vectors (default 3072 for text-embedding-3-large)

        Returns:
            Collection name that was created/verified
        """
        collection_name = self.name_manager.generate_collection_name(document_filename)

        if not self.collection_exists(collection_name):
            self._create_collection(collection_name, vector_size)
            print(f"🆕 Created collection: {collection_name}")
        else:
            collection_info = self.client.get_collection(collection_name)
            print(f"✅ Collection '{collection_name}' exists with {collection_info.points_count} points")

        return collection_name

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists"""
        return self.client.collection_exists(collection_name)

    def get_collection_for_document(self, document_filename: str) -> str:
        """Get the collection name for a document (without creating it)"""
        return self.name_manager.generate_collection_name(document_filename)

    def delete_document_collection(self, document_filename: str) -> bool:
        """
        Delete the entire collection for a document

        Args:
            document_filename: Name of the document

        Returns:
            True if deletion successful, False otherwise
        """
        collection_name = self.name_manager.generate_collection_name(document_filename)

        if not self.collection_exists(collection_name):
            print(f"📭 Collection '{collection_name}' does not exist")
            return True  # Nothing to delete is success

        try:
            self.client.delete_collection(collection_name)
            print(f"🗑️ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection {collection_name}: {str(e)}")
            return False

    def list_all_rag_collections(self) -> Set[str]:
        """
        List all RAG collections in Qdrant

        Returns:
            Set of RAG collection names
        """
        try:
            all_collections_response = self.client.get_collections()
            all_collection_names = {col.name for col in all_collections_response.collections}

            # Filter to only RAG collections
            rag_collections = self.name_manager.get_all_rag_collections(all_collection_names)

            return rag_collections
        except Exception as e:
            print(f"⚠️ Error listing collections: {str(e)}")
            return set()

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            if not self.collection_exists(collection_name):
                return {"exists": False}

            collection_info = self.client.get_collection(collection_name)

            return {
                "exists": True,
                "name": collection_name,
                "points_count": collection_info.points_count,
                "document_name": self.name_manager.extract_document_name_from_collection(collection_name)
            }
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }

    def _create_collection(self, collection_name: str, vector_size: int) -> None:
        """
        Create a new collection with specified vector size

        Args:
            collection_name: Name of the collection
            vector_size: Size of vectors
        """
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
