"""
Log Analysis Agent: Ingests application logs, detects error patterns,
clusters related errors, and links them to active incidents.
Uses Claude AI for intelligent log parsing and pattern recognition.
"""
import re
import json
import logging
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional

from base_agent import BaseAgent
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

# Common error patterns for fast rule-based detection
ERROR_PATTERNS = [
    {"pattern": r"OutOfMemoryError|OOM|oom-killer", "category": "memory", "severity": "critical"},
    {"pattern": r"Connection refused|ECONNREFUSED|connection reset", "category": "connectivity", "severity": "high"},
    {"pattern": r"TimeoutError|timeout|timed out|deadline exceeded", "category": "timeout", "severity": "high"},
    {"pattern": r"disk full|no space left|ENOSPC", "category": "disk", "severity": "critical"},
    {"pattern": r"permission denied|EACCES|403 Forbidden", "category": "permission", "severity": "medium"},
    {"pattern": r"404 Not Found|route not found", "category": "not_found", "severity": "low"},
    {"pattern": r"500 Internal Server Error|502 Bad Gateway|503 Service Unavailable", "category": "server_error", "severity": "high"},
    {"pattern": r"SSL|TLS|certificate|CERT_", "category": "ssl", "severity": "high"},
    {"pattern": r"authentication failed|invalid token|jwt expired|unauthorized", "category": "auth", "severity": "medium"},
    {"pattern": r"deadlock|lock timeout|lock wait", "category": "database", "severity": "critical"},
    {"pattern": r"segfault|segmentation fault|SIGSEGV|core dump", "category": "crash", "severity": "critical"},
    {"pattern": r"rate limit|throttl|429 Too Many", "category": "rate_limit", "severity": "medium"},
    {"pattern": r"DNS|name resolution|NXDOMAIN", "category": "dns", "severity": "high"},
    {"pattern": r"CPU.*100%|cpu spike|high cpu|load average", "category": "cpu", "severity": "high"},
]

LOG_LEVELS = {"FATAL": 5, "ERROR": 4, "WARN": 3, "WARNING": 3, "INFO": 2, "DEBUG": 1}


class LogAnalysisAgent(BaseAgent):
    """Analyzes application logs to detect errors, patterns, and anomalies."""

    def __init__(self):
        super().__init__("LogAnalysisAgent")
        self._log_buffer: List[Dict] = []
        self._error_clusters: Dict[str, List[Dict]] = defaultdict(list)
        self._pattern_counts: Counter = Counter()
        self._last_analysis = datetime.now(timezone.utc)
        self._analysis_interval = 120  # Analyze every 2 minutes
        self._processed_count = 0

    def tick(self):
        """Fetch new logs from backend, analyze them, and report findings."""
        try:
            # Fetch recent logs
            logs = self.api_get("/logs/recent", {"limit": 100, "since_minutes": 3})
            if isinstance(logs, dict):
                logs = logs.get("logs", [])
        except Exception:
            # If no log endpoint exists yet, use buffered logs
            logs = self._log_buffer
            self._log_buffer = []

        if not logs:
            return

        # Process each log entry
        errors = []
        warnings = []

        for log in logs:
            parsed = self._parse_log(log)
            if not parsed:
                continue

            self._processed_count += 1

            if parsed["level"] in ("ERROR", "FATAL", "CRITICAL"):
                errors.append(parsed)
                self._classify_error(parsed)
            elif parsed["level"] in ("WARN", "WARNING"):
                warnings.append(parsed)

        # Cluster errors and detect patterns
        if errors:
            clusters = self._cluster_errors(errors)
            for cluster_key, cluster_errors in clusters.items():
                if len(cluster_errors) >= 3:
                    # Error burst detected — report it
                    self._report_error_burst(cluster_key, cluster_errors)

        # Periodic deep analysis with AI
        now = datetime.now(timezone.utc)
        if (now - self._last_analysis).total_seconds() >= self._analysis_interval:
            self._last_analysis = now
            if self._error_clusters:
                self._ai_analysis()

    def ingest_log(self, log_entry: Dict[str, Any]):
        """Accept a single log entry for analysis."""
        self._log_buffer.append(log_entry)

    def ingest_batch(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Accept a batch of logs and return immediate analysis."""
        errors = []
        warnings = []
        parsed_logs = []

        for log in logs:
            parsed = self._parse_log(log)
            if not parsed:
                continue
            parsed_logs.append(parsed)
            self._processed_count += 1

            if parsed["level"] in ("ERROR", "FATAL", "CRITICAL"):
                errors.append(parsed)
                self._classify_error(parsed)
            elif parsed["level"] in ("WARN", "WARNING"):
                warnings.append(parsed)

        # Cluster errors
        clusters = self._cluster_errors(errors) if errors else {}

        # Find patterns
        patterns = []
        for cluster_key, cluster_errors in clusters.items():
            category = cluster_errors[0].get("category", "unknown")
            severity = max((e.get("severity_score", 0) for e in cluster_errors), default=0)
            patterns.append({
                "pattern": cluster_key,
                "category": category,
                "count": len(cluster_errors),
                "severity": "critical" if severity >= 5 else "high" if severity >= 4 else "medium",
                "first_seen": cluster_errors[0].get("timestamp", ""),
                "last_seen": cluster_errors[-1].get("timestamp", ""),
                "sample_message": cluster_errors[0].get("message", "")[:200],
            })

        return {
            "total_processed": len(parsed_logs),
            "errors": len(errors),
            "warnings": len(warnings),
            "error_patterns": sorted(patterns, key=lambda p: p["count"], reverse=True),
            "top_error_categories": dict(self._pattern_counts.most_common(5)),
            "recommendations": self._generate_recommendations(patterns),
        }

    def _parse_log(self, log: Any) -> Optional[Dict]:
        """Parse a log entry (string or dict) into structured format."""
        if isinstance(log, str):
            return self._parse_log_string(log)
        elif isinstance(log, dict):
            return {
                "timestamp": log.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "level": log.get("level", "INFO").upper(),
                "service": log.get("service", "unknown"),
                "message": log.get("message", str(log)),
                "source": log.get("source", ""),
                "raw": log,
                "severity_score": LOG_LEVELS.get(log.get("level", "INFO").upper(), 2),
            }
        return None

    def _parse_log_string(self, line: str) -> Optional[Dict]:
        """Parse a raw log string into structured format."""
        # Common log formats
        patterns = [
            # ISO timestamp + level: 2024-01-15T10:30:00Z ERROR [service] message
            r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*Z?)\s+(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\s+\[?(?P<service>\w+)?\]?\s*(?P<message>.*)",
            # Syslog-ish: Jan 15 10:30:00 host service[pid]: message
            r"(?P<timestamp>\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+\S+\s+(?P<service>\w+)\[?\d*\]?:\s*(?P<message>.*)",
            # Simple: [ERROR] message
            r"\[(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]\s*(?P<message>.*)",
        ]

        for pat in patterns:
            m = re.match(pat, line.strip(), re.IGNORECASE)
            if m:
                d = m.groupdict()
                level = d.get("level", "INFO").upper()
                return {
                    "timestamp": d.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "level": level,
                    "service": d.get("service", "unknown"),
                    "message": d.get("message", line),
                    "source": "raw_log",
                    "severity_score": LOG_LEVELS.get(level, 2),
                }

        # Fallback — treat as INFO
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "service": "unknown",
            "message": line.strip(),
            "source": "raw_log",
            "severity_score": 2,
        }

    def _classify_error(self, parsed_log: Dict):
        """Classify an error by matching against known patterns."""
        message = parsed_log.get("message", "")
        for ep in ERROR_PATTERNS:
            if re.search(ep["pattern"], message, re.IGNORECASE):
                parsed_log["category"] = ep["category"]
                parsed_log["matched_pattern"] = ep["pattern"]
                self._pattern_counts[ep["category"]] += 1
                self._error_clusters[ep["category"]].append(parsed_log)
                return

        # Unknown error
        parsed_log["category"] = "unknown"
        self._pattern_counts["unknown"] += 1
        self._error_clusters["unknown"].append(parsed_log)

    def _cluster_errors(self, errors: List[Dict]) -> Dict[str, List[Dict]]:
        """Group errors by similarity (service + category)."""
        clusters: Dict[str, List[Dict]] = defaultdict(list)
        for err in errors:
            key = f"{err.get('service', 'unknown')}:{err.get('category', 'unknown')}"
            clusters[key].append(err)
        return clusters

    def _report_error_burst(self, cluster_key: str, errors: List[Dict]):
        """Report an error burst to the backend as a potential incident."""
        service, category = cluster_key.split(":", 1) if ":" in cluster_key else (cluster_key, "unknown")
        severity = max((e.get("severity_score", 0) for e in errors), default=0)
        severity_name = "critical" if severity >= 5 else "high" if severity >= 4 else "medium"

        try:
            self.api_post("/alerts", {
                "title": f"Error burst: {category} in {service}",
                "message": f"{len(errors)} {category} errors detected in {service} within analysis window. Sample: {errors[0].get('message', '')[:200]}",
                "severity": severity_name,
                "source": "log_analysis_agent",
                "metadata": {
                    "error_count": len(errors),
                    "category": category,
                    "service": service,
                    "first_error": errors[0].get("timestamp", ""),
                    "last_error": errors[-1].get("timestamp", ""),
                },
            })
            print(f"  [LogAgent] Error burst reported: {len(errors)}x {category} in {service}")
        except Exception as e:
            logger.warning(f"Failed to report error burst: {e}")

    def _ai_analysis(self):
        """Use Claude AI to analyze error patterns and provide insights."""
        if not ANTHROPIC_API_KEY:
            return

        # Summarize clusters for AI
        summary = []
        for category, errors in self._error_clusters.items():
            if not errors:
                continue
            sample_msgs = [e.get("message", "")[:150] for e in errors[:5]]
            services = set(e.get("service", "unknown") for e in errors)
            summary.append({
                "category": category,
                "count": len(errors),
                "services": list(services),
                "samples": sample_msgs,
            })

        if not summary:
            return

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze these application error patterns from the last analysis window and provide:
1. Root cause hypothesis for each cluster
2. Correlations between clusters (are they related?)
3. Priority ranking
4. Recommended actions

Error clusters:
{json.dumps(summary, indent=2)}

Respond in JSON format: {{"analysis": [{{"category": "", "root_cause": "", "priority": 1-5, "action": ""}}], "correlations": "", "overall_health": ""}}"""
                }],
            )

            result = response.content[0].text
            logger.info(f"AI log analysis complete: {result[:200]}")

            # Store analysis result
            try:
                self.api_post("/logs/analysis", {
                    "analysis": result,
                    "clusters_analyzed": len(summary),
                    "total_errors": sum(s["count"] for s in summary),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"AI log analysis failed: {e}")

        # Clear clusters after analysis
        self._error_clusters.clear()
        self._pattern_counts.clear()

    def _generate_recommendations(self, patterns: List[Dict]) -> List[str]:
        """Generate actionable recommendations from detected patterns."""
        recommendations = []
        for p in patterns[:5]:
            cat = p.get("category", "unknown")
            count = p.get("count", 0)

            recs = {
                "memory": f"Memory issues detected ({count}x) — check for memory leaks, increase heap size, or add memory limits",
                "connectivity": f"Connection errors ({count}x) — verify service health, check network policies, review firewall rules",
                "timeout": f"Timeout errors ({count}x) — increase timeout values, check downstream service latency, review connection pool settings",
                "disk": f"Disk space issues ({count}x) — clean up old logs/temp files, increase volume size, set up log rotation",
                "database": f"Database issues ({count}x) — check for long-running queries, review connection pool, check for deadlocks",
                "crash": f"Application crashes ({count}x) — review core dumps, check for null pointer dereferences, review recent deployments",
                "auth": f"Authentication failures ({count}x) — check token expiry, verify credentials, review auth service health",
                "ssl": f"SSL/TLS errors ({count}x) — check certificate expiry, verify CA chain, update TLS configuration",
                "cpu": f"CPU pressure ({count}x) — identify hot code paths, check for infinite loops, consider horizontal scaling",
                "rate_limit": f"Rate limiting ({count}x) — implement backoff, review API quotas, consider caching",
                "dns": f"DNS resolution failures ({count}x) — check DNS server health, verify domain configuration, review /etc/resolv.conf",
                "server_error": f"Server errors ({count}x) — check application logs for stack traces, review recent deployments, check resource usage",
            }

            if cat in recs:
                recommendations.append(recs[cat])
            elif cat != "unknown":
                recommendations.append(f"{cat} errors detected ({count}x) — investigate and address root cause")

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """Return agent statistics."""
        return {
            "processed_logs": self._processed_count,
            "active_clusters": len(self._error_clusters),
            "pattern_counts": dict(self._pattern_counts.most_common(10)),
            "buffered_logs": len(self._log_buffer),
            "last_analysis": self._last_analysis.isoformat(),
        }
