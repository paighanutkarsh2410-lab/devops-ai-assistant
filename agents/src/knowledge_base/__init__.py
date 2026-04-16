"""Knowledge Base module: Qdrant vector DB + embeddings for incident learning."""
from .qdrant_client import QdrantKnowledgeBase
from .embeddings import generate_embedding, generate_incident_embedding, EmbeddingCache

__all__ = [
    "QdrantKnowledgeBase",
    "generate_embedding",
    "generate_incident_embedding",
    "EmbeddingCache",
]
