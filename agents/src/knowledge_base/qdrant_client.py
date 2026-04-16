"""
Qdrant Vector Database client for incident knowledge base.
Stores incident embeddings and performs similarity search for pattern matching.

Setup:
  1. Create free account at https://cloud.qdrant.io
  2. Create a cluster (free tier: 1GB storage, 1M vectors)
  3. Get API key from cluster dashboard
  4. Set QDRANT_URL and QDRANT_API_KEY in agents/.env
"""
import os
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
VECTOR_SIZE = 384  # sentence-transformers all-MiniLM-L6-v2

# Graceful import
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue,
        PayloadSchemaType, TextIndexParams, TokenizerType,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not installed. pip install qdrant-client")


class QdrantKnowledgeBase:
    """Vector database for storing and searching incident knowledge."""

    INCIDENTS_COLLECTION = "incidents"
    SOLUTIONS_COLLECTION = "solutions"

    def __init__(self):
        self._client = None
        self._initialized = False

    def _get_client(self) -> Optional[Any]:
        """Lazy-initialize Qdrant client."""
        if self._client is not None:
            return self._client

        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant client not available")
            return None

        if not QDRANT_URL:
            logger.warning("QDRANT_URL not configured — using in-memory storage")
            self._client = QdrantClient(":memory:")
        else:
            self._client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY if QDRANT_API_KEY else None,
                timeout=10,
            )

        if not self._initialized:
            self.initialize_collections()
            self._initialized = True

        return self._client

    def initialize_collections(self):
        """Create collections with indexes if they don't exist."""
        client = self._client
        if not client:
            return

        for collection_name in [self.INCIDENTS_COLLECTION, self.SOLUTIONS_COLLECTION]:
            try:
                collections = [c.name for c in client.get_collections().collections]
                if collection_name not in collections:
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=VECTOR_SIZE,
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"Created collection: {collection_name}")

                    # Create payload indexes for fast filtering
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="service_name",
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="severity",
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="success",
                        field_schema=PayloadSchemaType.BOOL,
                    )
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="root_cause",
                        field_schema=TextIndexParams(
                            type="text",
                            tokenizer=TokenizerType.WORD,
                            min_token_len=2,
                            max_token_len=20,
                            lowercase=True,
                        ),
                    )
                    logger.info(f"Created indexes for: {collection_name}")
                else:
                    logger.info(f"Collection already exists: {collection_name}")

            except Exception as e:
                logger.error(f"Failed to init collection {collection_name}: {e}")

    def store_incident(self, incident_data: dict, embedding: List[float]) -> bool:
        """
        Store an incident with its embedding in Qdrant.

        Args:
            incident_data: Dict with incident_id, service_name, root_cause, etc.
            embedding: 384-dim vector from sentence-transformers.
        """
        client = self._get_client()
        if not client:
            return False

        incident_id = incident_data.get("incident_id", "")
        if not incident_id:
            logger.warning("No incident_id provided, skipping store")
            return False

        payload = {
            "incident_id": str(incident_id),
            "service_name": incident_data.get("service_name", ""),
            "root_cause": incident_data.get("root_cause", ""),
            "solution": incident_data.get("solution", ""),
            "resolution_time": incident_data.get("resolution_time", 0),
            "success": incident_data.get("success", True),
            "severity": incident_data.get("severity", "medium"),
            "timestamp": incident_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "title": incident_data.get("title", ""),
            "description": incident_data.get("description", ""),
            "action_taken": incident_data.get("action_taken", ""),
            "pattern_type": incident_data.get("pattern_type", ""),
        }

        # Use hash of incident_id as point ID for idempotent upserts
        point_id = abs(hash(str(incident_id))) % (2**63)

        try:
            client.upsert(
                collection_name=self.INCIDENTS_COLLECTION,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
            logger.info(f"Stored incident {incident_id} in knowledge base")
            return True
        except Exception as e:
            logger.error(f"Failed to store incident: {e}")
            return self._retry_once(
                lambda: client.upsert(
                    collection_name=self.INCIDENTS_COLLECTION,
                    points=[PointStruct(id=point_id, vector=embedding, payload=payload)],
                )
            )

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.7,
        service_filter: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar incidents by embedding vector.

        Args:
            query_embedding: 384-dim query vector.
            top_k: Number of results.
            min_score: Minimum cosine similarity (0-1).
            service_filter: Optional service name filter.

        Returns:
            List of dicts with payload + score, sorted by similarity.
        """
        client = self._get_client()
        if not client:
            return []

        query_filter = None
        if service_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="service_name",
                        match=MatchValue(value=service_filter),
                    )
                ]
            )

        try:
            results = client.query_points(
                collection_name=self.INCIDENTS_COLLECTION,
                query=query_embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            ).points

            similar = []
            for hit in results:
                score = hit.score
                if score >= min_score:
                    entry = dict(hit.payload) if hit.payload else {}
                    entry["score"] = round(score, 4)
                    similar.append(entry)

            return similar

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific incident from the vector DB."""
        client = self._get_client()
        if not client:
            return None

        try:
            results = client.scroll(
                collection_name=self.INCIDENTS_COLLECTION,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="incident_id",
                            match=MatchValue(value=str(incident_id)),
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )

            points = results[0]
            if points:
                return dict(points[0].payload) if points[0].payload else None
            return None

        except Exception as e:
            logger.error(f"Failed to get incident {incident_id}: {e}")
            return None

    def update_incident_success(self, incident_id: str, success: bool) -> bool:
        """Update the success flag after remediation outcome is known."""
        client = self._get_client()
        if not client:
            return False

        point_id = abs(hash(str(incident_id))) % (2**63)

        try:
            client.set_payload(
                collection_name=self.INCIDENTS_COLLECTION,
                payload={"success": success},
                points=[point_id],
            )
            logger.info(f"Updated incident {incident_id} success={success}")
            return True
        except Exception as e:
            logger.error(f"Failed to update success flag: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get stats about the knowledge base."""
        client = self._get_client()
        if not client:
            return {"available": False}

        try:
            info = client.get_collection(self.INCIDENTS_COLLECTION)
            return {
                "available": True,
                "total_incidents": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors": info.indexed_vectors_count,
                "status": info.status.value if info.status else "unknown",
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

    def delete_incident(self, incident_id: str) -> bool:
        """Remove an incident from the knowledge base."""
        client = self._get_client()
        if not client:
            return False

        point_id = abs(hash(str(incident_id))) % (2**63)
        try:
            client.delete(
                collection_name=self.INCIDENTS_COLLECTION,
                points_selector=[point_id],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete incident: {e}")
            return False

    def _retry_once(self, operation) -> bool:
        """Retry an operation once after a brief delay."""
        try:
            time.sleep(1)
            operation()
            return True
        except Exception as e:
            logger.error(f"Retry failed: {e}")
            return False
