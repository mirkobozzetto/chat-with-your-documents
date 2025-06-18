# src/vector_stores/qdrant_vector_store.py
import os
import socket
import urllib3
import time
from typing import List, Optional, Any, Callable
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.schema import Document
from .base_vector_store import BaseVectorStoreManager
from .custom_qdrant_client import CustomQdrantClient
from .qdrant_retriever import QdrantRetriever
from .qdrant_collection_manager import QdrantCollectionManager
from .collection_name_manager import CollectionNameManager

"""Force IPv4 for Qdrant connection"""
old_getaddrinfo = socket.getaddrinfo
def force_ipv4_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = force_ipv4_getaddrinfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class QdrantVectorStoreManager(BaseVectorStoreManager):

    def __init__(self, embeddings):
        super().__init__(embeddings)
        self.qdrant_url = os.getenv("QDRANT_URL", "https://qdrant.mirko.re")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))
        
        # Current document collection (will be set when processing a document)
        self.current_collection_name = None
        self.current_document_filename = None

        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY must be set in environment variables")

        print(f"🔗 Connecting to Qdrant: {self.qdrant_url}")
        self.client = CustomQdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=self.timeout
        )
        
        # Initialize collection manager
        self.collection_manager = QdrantCollectionManager(self.client)
        self.name_manager = CollectionNameManager()

        self.vector_store = self._load_existing_vector_store()

    def set_current_document(self, document_filename: str) -> None:
        """Set the current document being processed"""
        self.current_document_filename = document_filename
        self.current_collection_name = self.collection_manager.get_collection_for_document(document_filename)
        print(f"📄 Set current document: {document_filename} -> {self.current_collection_name}")

    def _create_vector_store_wrapper(self):
        print(f"🔗 Creating multi-collection vector store wrapper")

        class MultiCollectionQdrantWrapper:
            def __init__(self, client, collection_manager, embeddings, vector_store_manager):
                self._client = client
                self.collection_manager = collection_manager
                self.embeddings = embeddings
                self.vector_store_manager = vector_store_manager

            def as_retriever(self, **kwargs):
                # Get current document to determine which collection to use
                if hasattr(self.vector_store_manager, 'current_document_filename') and self.vector_store_manager.current_document_filename:
                    collection_name = self.collection_manager.get_collection_for_document(
                        self.vector_store_manager.current_document_filename
                    )
                    if self.collection_manager.collection_exists(collection_name):
                        print(f"🎯 Using collection for current document: {collection_name}")
                        return QdrantRetriever(self._client, collection_name, self.embeddings)
                
                # Fallback: use first available collection
                all_collections = self.collection_manager.list_all_rag_collections()
                if all_collections:
                    first_collection = next(iter(all_collections))
                    print(f"📋 Using first available collection: {first_collection}")
                    return QdrantRetriever(self._client, first_collection, self.embeddings)
                return None

            def add_documents(self, documents):
                print(f"📝 Adding {len(documents)} documents via multi-collection wrapper")

        wrapper = MultiCollectionQdrantWrapper(self.client, self.collection_manager, self.embeddings, self)
        print(f"✅ Created multi-collection wrapper successfully")
        return wrapper

    def _load_existing_vector_store(self) -> Optional[Any]:
        try:
            print("📡 Testing Qdrant connection with collection manager...")

            # List all RAG collections
            rag_collections = self.collection_manager.list_all_rag_collections()
            
            if rag_collections:
                print(f"✅ Connected to Qdrant with {len(rag_collections)} RAG collections:")
                for collection in rag_collections:
                    stats = self.collection_manager.get_collection_stats(collection)
                    document_name = stats.get('document_name', 'unknown')
                    points_count = stats.get('points_count', 0)
                    print(f"  📚 {collection}: {document_name} ({points_count} points)")

                return self._create_vector_store_wrapper()
            else:
                print(f"📭 No existing RAG collections found")
                return None

        except Exception as e:
            print(f"⚠️ Could not connect to Qdrant: {str(e)}")
            return None

    def has_documents(self) -> bool:
        try:
            rag_collections = self.collection_manager.list_all_rag_collections()
            for collection in rag_collections:
                stats = self.collection_manager.get_collection_stats(collection)
                if stats.get('points_count', 0) > 0:
                    return True
            return False
        except:
            return False

    def create_vector_store(self, chunks: List[Document], progress_callback: Optional[Callable] = None) -> None:
        if not self.current_document_filename:
            raise Exception("No current document set. Call set_current_document() first.")
        
        print(f"🗄️ Creating Qdrant vector store for document: {self.current_document_filename}")

        # Ensure collection exists for this document
        collection_name = self.collection_manager.ensure_document_collection_exists(
            self.current_document_filename, 
            vector_size=3072
        )

        if not self.vector_store:
            self.vector_store = self._create_vector_store_wrapper()

        print(f"📤 Adding {len(chunks)} chunks to collection: {collection_name}")

        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            print(f"📦 Processing batch {batch_num}/{total_batches}")

            try:
                embeddings = self._process_embeddings_batch([doc.page_content for doc in batch])

                points = []
                for j, (doc, embedding) in enumerate(zip(batch, embeddings)):
                    point = PointStruct(
                        id=i + j,
                        vector=embedding,
                        payload={
                            "page_content": doc.page_content,
                            "metadata": doc.metadata
                        }
                    )
                    points.append(point)

                self.client.upsert(collection_name, points)

                if progress_callback:
                    progress = 0.9 + (batch_num / total_batches) * 0.1
                    progress_callback(progress, f"Batch {batch_num}/{total_batches}")

                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error in batch {batch_num}: {str(e)}")
                raise

        print(f"✅ Qdrant vector store created with {len(chunks)} chunks in collection: {collection_name}")

    def _process_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        embedding_batch_size = 100
        all_embeddings = []

        for i in range(0, len(texts), embedding_batch_size):
            batch = texts[i:i + embedding_batch_size]
            embeddings = self.embeddings.embed_documents(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def get_vector_store(self) -> Optional[Any]:
        return self.vector_store

    def get_chunk_count(self) -> int:
        try:
            total_chunks = 0
            rag_collections = self.collection_manager.list_all_rag_collections()
            for collection in rag_collections:
                stats = self.collection_manager.get_collection_stats(collection)
                total_chunks += stats.get('points_count', 0)
            return total_chunks
        except:
            return 0

    def get_all_metadata(self) -> List[dict]:
        try:
            all_metadatas = []
            rag_collections = self.collection_manager.list_all_rag_collections()
            
            if not rag_collections:
                return []

            for collection_name in rag_collections:
                scroll_result = self.client.scroll(
                    collection_name=collection_name,
                    limit=10000,
                    with_payload=True,
                    with_vectors=False
                )

                for point in scroll_result[0]:
                    if point.payload and "metadata" in point.payload:
                        all_metadatas.append(point.payload["metadata"])

            print(f"📊 Retrieved {len(all_metadatas)} metadata records from {len(rag_collections)} collections")
            return all_metadatas

        except Exception as e:
            print(f"⚠️ Error getting metadata from Qdrant: {str(e)}")
            return []

    def delete_document(self, document_filename: str) -> bool:
        """Delete a document by deleting its entire collection"""
        try:
            print(f"🗑️ Deleting document collection for: {document_filename}")

            # Use the collection manager to delete the entire collection
            success = self.collection_manager.delete_document_collection(document_filename)

            if success:
                print(f"✅ Successfully deleted collection for document: {document_filename}")
                # Refresh vector store wrapper to reflect changes
                if self.vector_store:
                    self.vector_store = self._create_vector_store_wrapper()
            else:
                print(f"❌ Failed to delete collection for document: {document_filename}")

            return success

        except Exception as e:
            print(f"❌ Error deleting document {document_filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_document_chunk_count(self, document_filename: str) -> int:
        """Get number of chunks for a specific document"""
        try:
            collection_name = self.collection_manager.get_collection_for_document(document_filename)
            
            if not self.collection_manager.collection_exists(collection_name):
                return 0

            stats = self.collection_manager.get_collection_stats(collection_name)
            return stats.get('points_count', 0)

        except Exception as e:
            print(f"⚠️ Error counting chunks for {document_filename}: {str(e)}")
            return 0

    def get_connection_info(self) -> dict:
        try:
            rag_collections = self.collection_manager.list_all_rag_collections()
            total_points = 0
            
            for collection in rag_collections:
                stats = self.collection_manager.get_collection_stats(collection)
                total_points += stats.get('points_count', 0)
            
            return {
                "url": self.qdrant_url,
                "collections": list(rag_collections),
                "total_collections": len(rag_collections),
                "total_points": total_points,
                "client_type": "custom_requests_multi_collection",
                "status": "connected"
            }
        except Exception as e:
            return {
                "url": self.qdrant_url,
                "collections": [],
                "client_type": "custom_requests_multi_collection",
                "error": str(e),
                "status": "error"
            }
