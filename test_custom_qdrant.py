# test_custom_qdrant.py
import os
import time
import sys
from dotenv import load_dotenv

from src.vector_stores.custom_qdrant_client import CustomQdrantClient
from src.vector_stores.qdrant_vector_store import QdrantVectorStoreManager

load_dotenv()

def test_custom_qdrant():
    print("🔍 Testing Custom Qdrant Client (based on requests)...")

    start_time = time.time()

    try:
        client = CustomQdrantClient(
            url=os.getenv("QDRANT_URL", "https://qdrant.mirko.re"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=30
        )

        print("📡 Getting collections...")
        collections = client.get_collections()

        connection_time = time.time() - start_time
        print(f"✅ SUCCESS! Custom client worked in {connection_time:.2f} seconds")
        print(f"📊 Collections found: {len(collections.collections)}")

        if collections.collections:
            for collection in collections.collections:
                print(f"   - {collection.name}")
        else:
            print("   - No collections yet")

        client.close()
        return True

    except Exception as e:
        connection_time = time.time() - start_time
        print(f"❌ FAILED after {connection_time:.2f} seconds")
        print(f"💥 Error: {str(e)}")
        return False

def test_vector_store_manager():
    print("\n🔍 Testing Vector Store Manager with Custom Client...")

    start_time = time.time()

    try:
        from langchain_openai import OpenAIEmbeddings
        from vector_stores.qdrant_vector_store import QdrantVectorStoreManager

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=os.getenv("OPENAI_API_KEY")
        )

        print("📡 Initializing vector store manager...")
        manager = QdrantVectorStoreManager(embeddings)

        connection_time = time.time() - start_time
        print(f"✅ SUCCESS! Manager initialized in {connection_time:.2f} seconds")

        chunk_count = manager.get_chunk_count()
        print(f"📊 Current chunk count: {chunk_count}")

        return True

    except Exception as e:
        connection_time = time.time() - start_time
        print(f"❌ FAILED after {connection_time:.2f} seconds")
        print(f"💥 Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Custom Qdrant Implementation...\n")

    test1 = test_custom_qdrant()

    if test1:
        test2 = test_vector_store_manager()

    print("\n🏁 Tests complete!")
