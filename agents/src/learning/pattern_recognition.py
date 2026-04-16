"""
Pattern Recognition: Identifies recurring incident patterns using clustering
and statistical analysis of incident embeddings and metadata.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """Discovers and classifies incident patterns from historical data."""

    # Pattern type definitions
    PATTERN_TYPES = {
        "memory_leak": {
            "keywords": ["memory", "oom", "out of memory", "heap", "leak", "gc"],
            "metrics": ["memory"],
            "description": "Memory exhaustion or leak pattern",
        },
        "cpu_spike": {
            "keywords": ["cpu", "high cpu", "processor", "compute", "thread"],
            "metrics": ["cpu"],
            "description": "CPU utilization spike pattern",
        },
        "api_timeout": {
            "keywords": ["timeout", "latency", "slow", "response time", "503", "504"],
            "metrics": ["response_time", "error_rate"],
            "description": "API timeout or high latency pattern",
        },
        "disk_full": {
            "keywords": ["disk", "storage", "space", "inode", "filesystem"],
            "metrics": ["disk"],
            "description": "Disk space exhaustion pattern",
        },
        "database_slow": {
            "keywords": ["database", "query", "connection pool", "deadlock", "postgres"],
            "metrics": ["response_time"],
            "description": "Database performance degradation pattern",
        },
        "deployment_issue": {
            "keywords": ["deploy", "rollback", "version", "release", "canary"],
            "metrics": ["error_rate"],
            "description": "Post-deployment failure pattern",
        },
        "cache_issue": {
            "keywords": ["cache", "redis", "stale", "miss", "eviction"],
            "metrics": ["response_time"],
            "description": "Cache miss or corruption pattern",
        },
        "network_issue": {
            "keywords": ["network", "dns", "connection refused", "socket", "tcp"],
            "metrics": ["error_rate"],
            "description": "Network connectivity pattern",
        },
        "process_stuck": {
            "keywords": ["stuck", "zombie", "hung", "unresponsive", "deadlock"],
            "metrics": ["cpu", "error_rate"],
            "description": "Process hang or deadlock pattern",
        },
    }

    def __init__(self):
        self._incident_history = []
        self._discovered_patterns = {}

    def extract_incident_pattern(self, incident: dict) -> Dict[str, Any]:
        """
        Extract a structured pattern from a single incident.

        Returns:
            Dict with pattern_type, symptoms, confidence, time_info, etc.
        """
        title = (incident.get("title", "") or "").lower()
        description = (incident.get("description", "") or "").lower()
        root_cause = (incident.get("root_cause", "") or "").lower()
        text = f"{title} {description} {root_cause}"

        # Classify pattern type
        pattern_type = "unknown"
        match_score = 0
        for ptype, info in self.PATTERN_TYPES.items():
            matches = sum(1 for kw in info["keywords"] if kw in text)
            if matches > match_score:
                match_score = matches
                pattern_type = ptype

        # Extract time information
        detected_at = incident.get("detected_at", "")
        time_info = self._extract_time_info(detected_at)

        # Build symptom list
        symptoms = {
            "metric_spikes": self._extract_metric_spikes(incident),
            "error_keywords": self._extract_error_keywords(text),
            "time_of_day": time_info.get("hour_bucket", "unknown"),
            "day_of_week": time_info.get("day_of_week", "unknown"),
            "service": incident.get("service_name", ""),
            "severity": incident.get("severity", ""),
        }

        confidence = min(match_score * 25, 95) if pattern_type != "unknown" else 10

        return {
            "pattern_type": pattern_type,
            "symptoms": symptoms,
            "confidence": confidence,
            "root_cause": incident.get("root_cause", ""),
            "solution": incident.get("solution", ""),
            "service_name": incident.get("service_name", ""),
            "time_info": time_info,
        }

    def find_pattern_clusters(
        self, incidents: List[dict], embeddings: Optional[List[List[float]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Group similar incidents into clusters using DBSCAN on embeddings.
        Falls back to keyword-based clustering if embeddings unavailable.
        """
        if not incidents:
            return []

        if embeddings and len(embeddings) == len(incidents):
            return self._cluster_by_embeddings(incidents, embeddings)

        return self._cluster_by_keywords(incidents)

    def calculate_pattern_frequency(
        self, incidents: List[dict]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate how often each pattern occurs and whether it's trending.
        """
        pattern_counts = defaultdict(lambda: {
            "count": 0, "recent_count": 0, "timestamps": []
        })

        now = datetime.now(timezone.utc)

        for inc in incidents:
            pattern = self.extract_incident_pattern(inc)
            ptype = pattern["pattern_type"]
            pattern_counts[ptype]["count"] += 1

            ts = inc.get("detected_at", "")
            if ts:
                pattern_counts[ptype]["timestamps"].append(ts)

                # Count recent (last 7 days)
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))
                    if (now - dt).days <= 7:
                        pattern_counts[ptype]["recent_count"] += 1
                except (ValueError, TypeError):
                    pass

        # Calculate trending
        result = {}
        for ptype, data in pattern_counts.items():
            total = data["count"]
            recent = data["recent_count"]

            # Trending: if recent activity is > 30% of total, it's increasing
            if total >= 3:
                ratio = recent / total
                if ratio > 0.5:
                    trending = "increasing"
                elif ratio < 0.1:
                    trending = "decreasing"
                else:
                    trending = "stable"
            else:
                trending = "stable"

            result[ptype] = {
                "count": total,
                "recent_count": recent,
                "trending": trending,
                "description": self.PATTERN_TYPES.get(ptype, {}).get("description", ""),
            }

        return dict(sorted(result.items(), key=lambda x: x[1]["count"], reverse=True))

    def link_patterns_to_causes(
        self, incidents: List[dict]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build pattern → root cause mappings with confidence scores.
        """
        pattern_causes = defaultdict(lambda: defaultdict(int))

        for inc in incidents:
            pattern = self.extract_incident_pattern(inc)
            ptype = pattern["pattern_type"]
            root_cause = inc.get("root_cause", "")
            if root_cause and ptype != "unknown":
                pattern_causes[ptype][root_cause] += 1

        result = {}
        for ptype, causes in pattern_causes.items():
            total = sum(causes.values())
            ranked_causes = sorted(causes.items(), key=lambda x: x[1], reverse=True)

            result[ptype] = {
                "total_incidents": total,
                "causes": [
                    {
                        "root_cause": cause,
                        "count": count,
                        "probability": round(count / total * 100, 1),
                    }
                    for cause, count in ranked_causes[:5]
                ],
            }

        return result

    # ── Internal Helpers ────────────────────────────────────────────────

    def _extract_time_info(self, timestamp_str: str) -> dict:
        """Extract time-based pattern info."""
        try:
            dt = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00").replace("+00:00", "")
            )
            hour = dt.hour
            if hour < 6:
                bucket = "night"
            elif hour < 12:
                bucket = "morning"
            elif hour < 18:
                bucket = "afternoon"
            else:
                bucket = "evening"

            return {
                "hour": hour,
                "hour_bucket": bucket,
                "day_of_week": dt.strftime("%A"),
                "is_weekend": dt.weekday() >= 5,
            }
        except (ValueError, TypeError):
            return {"hour_bucket": "unknown", "day_of_week": "unknown"}

    def _extract_metric_spikes(self, incident: dict) -> List[str]:
        """Identify which metrics likely spiked based on incident text."""
        text = f"{incident.get('title', '')} {incident.get('root_cause', '')}".lower()
        spikes = []
        metric_keywords = {
            "cpu": ["cpu", "processor", "compute"],
            "memory": ["memory", "ram", "heap", "oom"],
            "error_rate": ["error", "exception", "500", "503"],
            "response_time": ["latency", "timeout", "slow", "response"],
            "disk": ["disk", "storage", "inode"],
        }
        for metric, keywords in metric_keywords.items():
            if any(kw in text for kw in keywords):
                spikes.append(metric)
        return spikes

    def _extract_error_keywords(self, text: str) -> List[str]:
        """Extract key error phrases from incident text."""
        error_indicators = [
            "out of memory", "connection refused", "timeout", "disk full",
            "permission denied", "segfault", "null pointer", "deadlock",
            "rate limited", "circuit breaker", "health check failed",
            "pod crashloopbackoff", "oom killed", "connection pool exhausted",
        ]
        return [kw for kw in error_indicators if kw in text]

    def _cluster_by_keywords(self, incidents: List[dict]) -> List[Dict[str, Any]]:
        """Cluster incidents by pattern type (keyword-based fallback)."""
        clusters = defaultdict(list)

        for inc in incidents:
            pattern = self.extract_incident_pattern(inc)
            ptype = pattern["pattern_type"]
            clusters[ptype].append({
                "incident_id": inc.get("id", ""),
                "title": inc.get("title", ""),
                "service_name": inc.get("service_name", ""),
                "severity": inc.get("severity", ""),
            })

        return [
            {
                "cluster_name": self.PATTERN_TYPES.get(ptype, {}).get(
                    "description", ptype
                ),
                "pattern_type": ptype,
                "incident_count": len(members),
                "incidents": members[:10],
            }
            for ptype, members in sorted(
                clusters.items(), key=lambda x: len(x[1]), reverse=True
            )
        ]

    def _cluster_by_embeddings(
        self, incidents: List[dict], embeddings: List[List[float]]
    ) -> List[Dict[str, Any]]:
        """Cluster incidents using DBSCAN on embeddings."""
        try:
            from sklearn.cluster import DBSCAN

            X = np.array(embeddings)
            clustering = DBSCAN(eps=0.3, min_samples=2, metric="cosine").fit(X)
            labels = clustering.labels_

            clusters = defaultdict(list)
            for i, label in enumerate(labels):
                cluster_key = f"cluster_{label}" if label >= 0 else "noise"
                clusters[cluster_key].append(incidents[i])

            result = []
            for key, members in clusters.items():
                if key == "noise":
                    continue

                # Name the cluster based on most common pattern type
                types = [self.extract_incident_pattern(m)["pattern_type"] for m in members]
                most_common = max(set(types), key=types.count) if types else "unknown"

                result.append({
                    "cluster_name": self.PATTERN_TYPES.get(most_common, {}).get(
                        "description", most_common
                    ),
                    "pattern_type": most_common,
                    "incident_count": len(members),
                    "incidents": [
                        {
                            "incident_id": m.get("id", ""),
                            "title": m.get("title", ""),
                            "service_name": m.get("service_name", ""),
                        }
                        for m in members[:10]
                    ],
                })

            return sorted(result, key=lambda x: x["incident_count"], reverse=True)

        except ImportError:
            logger.warning("scikit-learn not available, falling back to keyword clustering")
            return self._cluster_by_keywords(incidents)
