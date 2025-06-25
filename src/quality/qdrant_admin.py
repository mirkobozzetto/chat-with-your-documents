# src/quality/qdrant_admin.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CollectionInfo
import json


@dataclass
class CollectionStats:
    name: str
    points_count: int
    vector_size: int
    distance_metric: str
    indexed: bool
    segments_count: int
    disk_usage_bytes: int


@dataclass
class VectorPoint:
    id: str
    payload: Dict[str, Any]
    vector_preview: List[float]


class QdrantCollectionAdmin:

    def __init__(self, client: QdrantClient):
        self.client = client

    def list_all_collections(self) -> List[CollectionStats]:
        collections = self.client.get_collections()
        stats = []

        for collection in collections.collections:
            collection_info = self.client.get_collection(collection.name)

            stats.append(CollectionStats(
                name=collection.name,
                points_count=collection_info.points_count,
                vector_size=collection_info.config.params.vectors.size,
                distance_metric=collection_info.config.params.vectors.distance.name,
                indexed=collection_info.status == "green",
                segments_count=len(collection_info.segments),
                disk_usage_bytes=self._estimate_disk_usage(collection_info)
            ))

        return stats

    def inspect_collection(self, collection_name: str) -> Dict[str, Any]:
        if not self.collection_exists(collection_name):
            return {"error": f"Collection '{collection_name}' not found"}

        collection_info = self.client.get_collection(collection_name)
        sample_points = self._get_sample_points(collection_name, limit=5)

        return {
            "name": collection_name,
            "status": collection_info.status,
            "points_count": collection_info.points_count,
            "vector_config": {
                "size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.name
            },
            "optimizer_config": collection_info.config.optimizer_config,
            "segments": len(collection_info.segments),
            "sample_points": sample_points,
            "payloads_schema": self._analyze_payloads_schema(collection_name)
        }

    def delete_collection(self, collection_name: str) -> bool:
        if not self.collection_exists(collection_name):
            return False

        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False

    def create_collection(self, collection_name: str, vector_size: int,
                         distance: Distance = Distance.COSINE) -> bool:
        if self.collection_exists(collection_name):
            return False

        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            return True
        except Exception:
            return False

    def collection_exists(self, collection_name: str) -> bool:
        try:
            self.client.get_collection(collection_name)
            return True
        except Exception:
            return False

    def clear_collection(self, collection_name: str) -> bool:
        if not self.collection_exists(collection_name):
            return False

        try:
            collection_info = self.client.get_collection(collection_name)
            vector_config = collection_info.config.params.vectors

            self.client.delete_collection(collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_config
            )
            return True
        except Exception:
            return False

    def get_collection_health(self, collection_name: str) -> Dict[str, Any]:
        if not self.collection_exists(collection_name):
            return {"status": "not_found"}

        collection_info = self.client.get_collection(collection_name)

        health_score = self._calculate_health_score(collection_info)

        return {
            "status": collection_info.status,
            "health_score": health_score,
            "points_count": collection_info.points_count,
            "segments_count": len(collection_info.segments),
            "indexed": collection_info.status == "green",
            "recommendations": self._generate_health_recommendations(collection_info)
        }

    def export_collection_metadata(self, collection_name: str) -> Dict[str, Any]:
        if not self.collection_exists(collection_name):
            return {}

        collection_info = self.client.get_collection(collection_name)

        return {
            "collection_name": collection_name,
            "vector_config": {
                "size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.name
            },
            "points_count": collection_info.points_count,
            "status": collection_info.status,
            "created_at": collection_info.created_at if hasattr(collection_info, 'created_at') else None,
            "segments": len(collection_info.segments)
        }

    def _get_sample_points(self, collection_name: str, limit: int = 5) -> List[VectorPoint]:
        try:
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_vectors=True,
                with_payload=True
            )

            points = []
            for point in scroll_result[0]:
                points.append(VectorPoint(
                    id=str(point.id),
                    payload=point.payload or {},
                    vector_preview=point.vector[:5] if point.vector else []
                ))

            return points
        except Exception:
            return []

    def _analyze_payloads_schema(self, collection_name: str) -> Dict[str, Any]:
        try:
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True
            )

            schema = {}
            for point in scroll_result[0]:
                if point.payload:
                    for key, value in point.payload.items():
                        if key not in schema:
                            schema[key] = {"type": type(value).__name__, "count": 0}
                        schema[key]["count"] += 1

            return schema
        except Exception:
            return {}

    def _estimate_disk_usage(self, collection_info: CollectionInfo) -> int:
        vector_size = collection_info.config.params.vectors.size
        points_count = collection_info.points_count

        vector_bytes = vector_size * 4
        estimated_payload_bytes = 200

        return (vector_bytes + estimated_payload_bytes) * points_count

    def _calculate_health_score(self, collection_info: CollectionInfo) -> float:
        score = 0.0

        if collection_info.status == "green":
            score += 40
        elif collection_info.status == "yellow":
            score += 20

        if collection_info.points_count > 0:
            score += 30

        if len(collection_info.segments) <= 5:
            score += 20
        elif len(collection_info.segments) <= 10:
            score += 10

        score += min(collection_info.points_count / 1000 * 10, 10)

        return min(score, 100.0)

    def _generate_health_recommendations(self, collection_info: CollectionInfo) -> List[str]:
        recommendations = []

        if collection_info.status != "green":
            recommendations.append("Collection non indexée - vérifier les ressources")

        if collection_info.points_count == 0:
            recommendations.append("Collection vide - ajouter des documents")

        if len(collection_info.segments) > 10:
            recommendations.append("Trop de segments - considérer l'optimisation")

        if not recommendations:
            recommendations.append("Collection en bonne santé")

        return recommendations
