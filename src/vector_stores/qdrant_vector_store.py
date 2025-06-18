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
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
        self.timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))

        if not self.qdrant_api_key:
            raise ValueError("QDRANT_API_KEY must be set in environment variables")

        print(f"🔗 Connecting to Qdrant: {self.qdrant_url}")
        self.client = CustomQdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=self.timeout
        )

        self._ensure_collection_exists()
        self.vector_store = self._load_existing_vector_store()

    def _ensure_collection_exists(self):
        """Ensure the collection exists and is properly configured"""
        try:
            print(f"🔍 Checking collection '{self.collection_name}'...")

            if self.client.collection_exists(self.collection_name):
                collection_info = self.client.get_collection(self.collection_name)
                print(f"✅ Collection '{self.collection_name}' exists with {collection_info.points_count} points")
                return True

            print(f"🆕 Creating new collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=3072,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created collection: {self.collection_name}")
            return True

        except Exception as e:
            print(f"❌ Error ensuring collection exists: {str(e)}")
            return False

    def _create_vector_store_wrapper(self):
        """Create a simple wrapper that uses the refactored retriever"""
        print(f"🔗 Creating lightweight vector store wrapper")

        class SimpleQdrantWrapper:
            def __init__(self, client, collection_name, embeddings):
                self._client = client
                self.collection_name = collection_name
                self.embeddings = embeddings

            def as_retriever(self, **kwargs):
                return QdrantRetriever(self._client, self.collection_name, self.embeddings)

            def add_documents(self, documents):
                print(f"📝 Adding {len(documents)} documents via wrapper")

        wrapper = SimpleQdrantWrapper(self.client, self.collection_name, self.embeddings)
        print(f"✅ Created lightweight wrapper successfully")
        return wrapper

    def _load_existing_vector_store(self) -> Optional[Any]:
        try:
            print("📡 Testing Qdrant connection with custom client...")

            if self.client.collection_exists(self.collection_name):
                collection_info = self.client.get_collection(self.collection_name)
                print(f"✅ Connected to existing Qdrant collection: {self.collection_name}")
                print(f"📊 Current points in collection: {collection_info.points_count}")

                return self._create_vector_store_wrapper()
            else:
                print(f"📭 No existing collection found: {self.collection_name}")
                return None

        except Exception as e:
            print(f"⚠️ Could not connect to Qdrant: {str(e)}")
            return None

    def has_documents(self) -> bool:
        try:
            if self.client.collection_exists(self.collection_name):
                collection_info = self.client.get_collection(self.collection_name)
                return collection_info.points_count > 0
        except:
            return False
        return False

    def create_vector_store(self, chunks: List[Document], progress_callback: Optional[Callable] = None) -> None:
        print("🗄️ Creating Qdrant vector store...")

        if not self._ensure_collection_exists():
            raise Exception("Failed to ensure collection exists")

        if not self.vector_store:
            self.vector_store = self._create_vector_store_wrapper()

        print("📤 Adding documents to Qdrant...")

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

                self.client.upsert(self.collection_name, points)

                if progress_callback:
                    progress = 0.9 + (batch_num / total_batches) * 0.1
                    progress_callback(progress, f"Batch {batch_num}/{total_batches}")

                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error in batch {batch_num}: {str(e)}")
                raise

        print(f"✅ Qdrant vector store created with {len(chunks)} chunks")

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
            if self.client.collection_exists(self.collection_name):
                collection_info = self.client.get_collection(self.collection_name)
                return collection_info.points_count
        except:
            return 0
        return 0

    def get_all_metadata(self) -> List[dict]:
        try:
            if not self.client.collection_exists(self.collection_name):
                return []

            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )

            metadatas = []
            print(f"🔍 Found {len(scroll_result[0])} points in collection")

            for point in scroll_result[0]:
                if point.payload:
                    print(f"📝 Point payload keys: {list(point.payload.keys())}")
                    if "metadata" in point.payload:
                        metadata = point.payload["metadata"]
                        print(f"📋 Metadata: {metadata}")
                        metadatas.append(metadata)

            print(f"📊 Total metadatas extracted: {len(metadatas)}")
            return metadatas

        except Exception as e:
            print(f"⚠️ Error getting metadata from Qdrant: {str(e)}")
            return []

    def get_connection_info(self) -> dict:
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "url": self.qdrant_url,
                "collection": self.collection_name,
                "points_count": collection_info.points_count,
                "client_type": "custom_requests",
                "status": "connected"
            }
        except Exception as e:
            return {
                "url": self.qdrant_url,
                "collection": self.collection_name,
                "client_type": "custom_requests",
                "error": str(e),
                "status": "error"
            }
