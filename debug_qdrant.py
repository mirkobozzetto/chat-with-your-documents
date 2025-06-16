# debug_qdrant.py
import os
import time
import socket
import urllib3
import httpx
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

old_getaddrinfo = socket.getaddrinfo
def force_ipv4_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = force_ipv4_getaddrinfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_qdrant_connection():
    print("🔍 Testing Qdrant connection with optimized settings...")

    start_time = time.time()

    try:
        client = QdrantClient(
            url=os.getenv("QDRANT_URL", "https://qdrant.mirko.re"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=30,
            https=True,
            verify=False,
            http2=False,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0
            ),
            follow_redirects=True
        )

        print("📡 Attempting to get collections...")
        collections = client.get_collections()

        connection_time = time.time() - start_time
        print(f"✅ SUCCESS! Connected in {connection_time:.2f} seconds")
        print(f"📊 Collections found: {len(collections.collections)}")

        if collections.collections:
            for collection in collections.collections:
                print(f"   - {collection.name}")
        else:
            print("   - No collections yet")

        return True

    except Exception as e:
        connection_time = time.time() - start_time
        print(f"❌ FAILED after {connection_time:.2f} seconds")
        print(f"💥 Error: {str(e)}")
        return False

def test_requests_fallback():
    print("\n🔄 Testing with requests library as fallback...")

    start_time = time.time()

    try:
        import requests

        response = requests.get(
            f"{os.getenv('QDRANT_URL', 'https://qdrant.mirko.re')}/collections",
            headers={"api-key": os.getenv("QDRANT_API_KEY")},
            timeout=(10, 30),
            verify=False
        )

        connection_time = time.time() - start_time
        print(f"✅ SUCCESS! requests worked in {connection_time:.2f} seconds")
        print(f"📊 Response: {response.json()}")
        return True

    except Exception as e:
        connection_time = time.time() - start_time
        print(f"❌ FAILED after {connection_time:.2f} seconds")
        print(f"💥 Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Qdrant connection debug tests...\n")

    test1 = test_qdrant_connection()

    if not test1:
        test_requests_fallback()

    print("\n🏁 Debug complete!")
