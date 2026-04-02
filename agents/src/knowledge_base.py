"""
Knowledge Base: Stores and searches past incidents for similar patterns.
Uses TF-IDF similarity for matching (no external vector DB required).
Can be upgraded to Qdrant for production use.
"""
import json
import os
import math
from collections import defaultdict
from typing import List, Optional


class KnowledgeBase:
    def __init__(self, storage_path: str = None):
        self._incidents = []
        self._storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), '..', 'data', 'knowledge_base.json'
        )
        self._load()

    def store_incident(self, incident: dict):
        """Store a resolved incident for future reference."""
        entry = {
            "id": incident.get("id", ""),
            "title": incident.get("title", ""),
            "description": incident.get("description", ""),
            "service_name": incident.get("service_name", ""),
            "severity": incident.get("severity", ""),
            "root_cause": incident.get("root_cause", ""),
            "solution": incident.get("solution", ""),
        }
        # Update if exists, else add
        for i, existing in enumerate(self._incidents):
            if existing["id"] == entry["id"]:
                self._incidents[i] = entry
                self._save()
                return
        self._incidents.append(entry)
        self._save()

    def search_similar(self, title: str, description: str = "",
                       service_name: str = "", top_k: int = 5) -> List[dict]:
        """
        Search for similar past incidents using text similarity.
        Returns top_k matches with similarity scores.
        """
        if not self._incidents:
            return []

        query = f"{title} {description} {service_name}".lower().split()
        results = []

        for inc in self._incidents:
            if not inc.get("root_cause"):
                continue  # Only match against resolved incidents

            doc = f"{inc['title']} {inc['description']} {inc['service_name']} {inc['root_cause']}".lower().split()
            score = self._similarity(query, doc)

            if score > 0.1:
                results.append({
                    "id": inc["id"],
                    "title": inc["title"],
                    "service_name": inc["service_name"],
                    "root_cause": inc["root_cause"],
                    "solution": inc["solution"],
                    "score": score,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _similarity(self, query_tokens: list, doc_tokens: list) -> float:
        """Simple cosine similarity using term frequency."""
        if not query_tokens or not doc_tokens:
            return 0.0

        all_tokens = set(query_tokens + doc_tokens)
        q_vec = [query_tokens.count(t) for t in all_tokens]
        d_vec = [doc_tokens.count(t) for t in all_tokens]

        dot = sum(a * b for a, b in zip(q_vec, d_vec))
        mag_q = math.sqrt(sum(a * a for a in q_vec))
        mag_d = math.sqrt(sum(a * a for a in d_vec))

        if mag_q == 0 or mag_d == 0:
            return 0.0
        return dot / (mag_q * mag_d)

    def _load(self):
        try:
            if os.path.exists(self._storage_path):
                with open(self._storage_path, 'r') as f:
                    self._incidents = json.load(f)
        except Exception:
            self._incidents = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, 'w') as f:
                json.dump(self._incidents, f, indent=2, default=str)
        except Exception as e:
            print(f"  [KB] Failed to save: {e}")
