# src/vector_stores/custom_qdrant_client.py
import requests
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client.models import VectorParams, PointStruct
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CustomQdrantClient:

    def __init__(self, url: str, api_key: str, timeout: int = 30):
        self.base_url = url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "api-key": api_key,
            "Content-Type": "application/json"
        })
        self.session.verify = False

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        kwargs['timeout'] = self.timeout

        if method == "PUT" and "json" in kwargs:
            print(f"🔍 Request URL: {url}")
            print(f"🔍 Request headers: {dict(self.session.headers)}")
            print(f"🔍 Request payload: {json.dumps(kwargs['json'], indent=2)[:500]}...")

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"❌ Response: {e.response.text}")
            raise

    def get_collections(self):
        result = self._request("GET", "/collections")
        print(f"🔍 Collections API response: {result}")

        class Collection:
            def __init__(self, name: str):
                self.name = name

        class CollectionsResponse:
            def __init__(self, collections_data):
                collections_list = collections_data.get('result', {}).get('collections', [])
                print(f"📝 Raw collections list: {collections_list}")

                self.collections = []
                for col in collections_list:
                    if isinstance(col, dict):
                        # API returns objects like {"name": "collection_name"}
                        collection_name = col.get('name', str(col))
                    else:
                        # API returns strings directly
                        collection_name = str(col)

                    self.collections.append(Collection(collection_name))

                print(f"📊 Parsed collections: {[c.name for c in self.collections]}")

        return CollectionsResponse(result)

    def get_collection(self, collection_name: str):
        result = self._request("GET", f"/collections/{collection_name}")

        class CollectionInfo:
            def __init__(self, data):
                self.points_count = data.get('result', {}).get('points_count', 0)

        return CollectionInfo(result)

    def collection_exists(self, collection_name: str) -> bool:
        try:
            print(f"🔍 Checking if collection '{collection_name}' exists...")
            self.get_collection(collection_name)
            print(f"✅ Collection '{collection_name}' exists")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ Collection '{collection_name}' does not exist (404)")
                return False
            print(f"⚠️ Unexpected error checking collection: {e}")
            raise
        except Exception as e:
            print(f"⚠️ Error checking collection: {e}")
            return False

    def create_collection(self, collection_name: str, vectors_config: VectorParams):
        payload = {
            "vectors": {
                "size": vectors_config.size,
                "distance": vectors_config.distance.value
            }
        }

        return self._request("PUT", f"/collections/{collection_name}", json=payload)

    def delete_collection(self, collection_name: str):
        return self._request("DELETE", f"/collections/{collection_name}")

    def upsert(self, collection_name: str, points: List[PointStruct]):
        payload = {
            "points": []
        }

        for point in points:
            point_data = {
                "id": int(point.id) if isinstance(point.id, (int, str)) and str(point.id).isdigit() else str(uuid.uuid4()),
                "vector": list(point.vector) if hasattr(point.vector, '__iter__') else point.vector,
                "payload": point.payload or {}
            }
            payload["points"].append(point_data)

        response = self._request("PUT", f"/collections/{collection_name}/points?wait=true", json=payload)
        print(f"✅ Upsert response: {response}")
        return response

    def scroll(self, collection_name: str, limit: int = 100, with_payload: bool = True, with_vectors: bool = False):
        params = {
            "limit": limit,
            "with_payload": with_payload,
            "with_vectors": with_vectors
        }

        result = self._request("POST", f"/collections/{collection_name}/points/scroll", json=params)

        class Point:
            def __init__(self, data):
                self.id = data.get('id')
                self.payload = data.get('payload', {})
                self.vector = data.get('vector')

        points_data = result.get('result', {}).get('points', [])
        points = [Point(p) for p in points_data]

        return (points, None)

    def search(self, collection_name: str, query_vector: List[float], limit: int = 10, with_payload: bool = True, filter: Optional[Dict] = None):
        payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": with_payload
        }

        if filter:
            payload["filter"] = filter

        result = self._request("POST", f"/collections/{collection_name}/points/search", json=payload)

        class ScoredPoint:
            def __init__(self, data):
                self.id = data.get('id')
                self.score = data.get('score')
                self.payload = data.get('payload', {})

        points_data = result.get('result', [])
        return [ScoredPoint(p) for p in points_data]

    def delete_points_by_filter(self, collection_name: str, filter_condition: Dict[str, Any]):
        """Delete points matching filter condition"""
        payload = {
            "filter": filter_condition,
            "wait": True
        }

        result = self._request("POST", f"/collections/{collection_name}/points/delete", json=payload)
        return result

    def count_points_by_filter(self, collection_name: str, filter_condition: Dict[str, Any]) -> int:
        """Count points matching filter condition"""
        payload = {
            "filter": filter_condition,
            "exact": True
        }

        try:
            result = self._request("POST", f"/collections/{collection_name}/points/count", json=payload)
            return result.get('result', {}).get('count', 0)
        except Exception as e:
            print(f"⚠️ Error counting points: {e}")
            return 0

    def close(self):
        self.session.close()

    def count(self, collection_name: str):
        """Get point count for compatibility with QdrantClient"""
        try:
            collection_info = self.get_collection(collection_name)

            class CountResult:
                def __init__(self, count):
                    self.count = count

            return CountResult(collection_info.points_count)
        except Exception as e:
            print(f"⚠️ Error getting count: {e}")
            return CountResult(0)
