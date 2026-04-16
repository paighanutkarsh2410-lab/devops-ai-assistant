"""
Embedding generator for incident text using sentence-transformers.
Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality).
Includes Redis caching to avoid recomputing identical text.
"""
import os
import json
import hashlib
import logging
import numpy as np
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_SIZE = 384
CACHE_TTL = 86400  # 24 hours

# Lazy-loaded model
_model = None


def _get_model():
    """Load the sentence-transformers model once at first use."""
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer

        cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
        os.makedirs(cache_dir, exist_ok=True)

        _model = SentenceTransformer(MODEL_NAME, cache_folder=cache_dir)
        logger.info(f"Loaded embedding model: {MODEL_NAME}")
        return _model
    except ImportError:
        logger.warning("sentence-transformers not installed. Using fallback hash embeddings.")
        return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


def _fallback_embedding(text: str) -> List[float]:
    """
    Deterministic hash-based embedding when sentence-transformers is unavailable.
    Not suitable for real similarity search, but keeps the system functional.
    """
    h = hashlib.sha384(text.encode()).digest()
    vec = [float(b) / 255.0 for b in h]
    # Pad/truncate to VECTOR_SIZE
    vec = (vec * ((VECTOR_SIZE // len(vec)) + 1))[:VECTOR_SIZE]
    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dim embedding for the given text.

    Args:
        text: Input text string.

    Returns:
        List of 384 floats (normalized vector).
    """
    if not text or not text.strip():
        return [0.0] * VECTOR_SIZE

    model = _get_model()
    if model is None:
        return _fallback_embedding(text)

    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return _fallback_embedding(text)


def generate_incident_embedding(incident: dict) -> List[float]:
    """
    Generate a weighted embedding combining multiple incident fields.

    Weights:
      - title: 0.4
      - description: 0.3
      - root_cause: 0.2
      - service_name: 0.1
    """
    fields = {
        "title": (incident.get("title", "") or "", 0.4),
        "description": (incident.get("description", "") or "", 0.3),
        "root_cause": (incident.get("root_cause", "") or "", 0.2),
        "service_name": (incident.get("service_name", "") or "", 0.1),
    }

    weighted_embedding = np.zeros(VECTOR_SIZE)
    total_weight = 0.0

    for field_name, (text, weight) in fields.items():
        if text.strip():
            emb = generate_embedding(text)
            weighted_embedding += np.array(emb) * weight
            total_weight += weight

    if total_weight > 0:
        weighted_embedding /= total_weight

    # Normalize the final vector
    norm = np.linalg.norm(weighted_embedding)
    if norm > 0:
        weighted_embedding = weighted_embedding / norm

    return weighted_embedding.tolist()


def batch_generate_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently using batching.

    Args:
        texts: List of input strings.
        batch_size: Number of texts per batch.

    Returns:
        List of embedding vectors.
    """
    if not texts:
        return []

    model = _get_model()
    if model is None:
        return [_fallback_embedding(t) for t in texts]

    try:
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return [_fallback_embedding(t) for t in texts]


class EmbeddingCache:
    """Redis-backed cache for embeddings to avoid recomputing identical text."""

    CACHE_PREFIX = "emb:"

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis
            self._redis = redis.from_url(REDIS_URL, decode_responses=True)
            self._redis.ping()
            return self._redis
        except Exception:
            self._redis = None
            return None

    def _cache_key(self, text: str) -> str:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self.CACHE_PREFIX}{text_hash}"

    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        r = self._get_redis()
        if not r:
            return None
        try:
            cached = r.get(self._cache_key(text))
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def set(self, text: str, embedding: List[float]):
        """Cache an embedding with TTL."""
        r = self._get_redis()
        if not r:
            return
        try:
            r.setex(
                self._cache_key(text),
                CACHE_TTL,
                json.dumps(embedding),
            )
        except Exception:
            pass

    def get_or_generate(self, text: str) -> List[float]:
        """Get from cache or generate and cache."""
        cached = self.get(text)
        if cached:
            return cached

        embedding = generate_embedding(text)
        self.set(text, embedding)
        return embedding
