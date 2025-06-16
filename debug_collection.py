# debug_collection.py
import os
import sys
from dotenv import load_dotenv

sys.path.append('./src/vector_stores')
from custom_qdrant_client import CustomQdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

def test_collection_operations():
    print("🚀 Testing Collection Operations...\n")

    client = CustomQdrantClient(
        url=os.getenv("QDRANT_URL", "https://qdrant.mirko.re"),
        api_key=os.getenv("QDRANT_API_KEY"),
        timeout=30
    )

    collection_name = "test_collection"

    print("1️⃣ Getting all collections...")
    collections = client.get_collections()
    print(f"Found {len(collections.collections)} collections\n")

    print("2️⃣ Checking if test collection exists...")
    exists = client.collection_exists(collection_name)
    print(f"Collection exists: {exists}\n")

    if exists:
        print("3️⃣ Deleting existing test collection...")
        try:
            client.delete_collection(collection_name)
            print("✅ Deleted successfully\n")
        except Exception as e:
            print(f"❌ Delete failed: {e}\n")

    print("4️⃣ Creating new test collection...")
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        print("✅ Created successfully\n")
    except Exception as e:
        print(f"❌ Create failed: {e}\n")
        return False

    print("5️⃣ Verifying collection exists...")
    exists_after = client.collection_exists(collection_name)
    print(f"Collection exists after creation: {exists_after}\n")

    print("6️⃣ Getting collections again...")
    collections_after = client.get_collections()
    print(f"Found {len(collections_after.collections)} collections after creation")
    for col in collections_after.collections:
        print(f"  - {col.name}")

    client.close()
    return True

if __name__ == "__main__":
    test_collection_operations()
