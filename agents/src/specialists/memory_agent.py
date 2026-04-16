"""
Memory Specialist Agent: Memory leak detection, heap analysis,
GC pressure, fragmentation, OOM prediction.
"""
import logging
from .base_specialist import BaseSpecialist, SpecialistReport, Finding

logger = logging.getLogger(__name__)


class MemorySpecialistAgent(BaseSpecialist):
    AGENT_TYPE = "memory"
    DOMAINS = ["memory", "performance"]
    ACTIONS = ["diagnose", "investigate", "predict"]

    MEM_WARN_PCT = 80
    MEM_CRITICAL_PCT = 92
    GC_PRESSURE_THRESHOLD = 15  # % time in GC

    def __init__(self):
        super().__init__("memory-specialist")

    def _perform_analysis(self, incident: dict, context: dict, report: SpecialistReport):
        service = incident.get("service_name", "unknown")

        self._detect_memory_leak(service, report)
        self._analyze_heap(service, report)
        self._check_gc_pressure(service, report)
        self._predict_oom(service, report)

    def _detect_memory_leak(self, service: str, report: SpecialistReport):
        # Simulated memory trend over 6 hours
        samples = [
            {"hour": 0, "rss_mb": 512}, {"hour": 1, "rss_mb": 540},
            {"hour": 2, "rss_mb": 575}, {"hour": 3, "rss_mb": 610},
            {"hour": 4, "rss_mb": 658}, {"hour": 5, "rss_mb": 712},
        ]

        growth_rate_mb_hr = (samples[-1]["rss_mb"] - samples[0]["rss_mb"]) / len(samples)
        is_leak = growth_rate_mb_hr > 20  # >20MB/hr is suspicious

        if is_leak:
            report.findings.append(Finding(
                category="memory_leak",
                severity="critical" if growth_rate_mb_hr > 50 else "high",
                title=f"Memory leak detected ({growth_rate_mb_hr:.0f} MB/hr growth)",
                description=f"RSS grew from {samples[0]['rss_mb']}MB to {samples[-1]['rss_mb']}MB over {len(samples)} hours",
                evidence=[
                    f"Growth rate: {growth_rate_mb_hr:.1f} MB/hr (monotonic increase)",
                    f"Start: {samples[0]['rss_mb']}MB → Current: {samples[-1]['rss_mb']}MB",
                    "No corresponding increase in request volume",
                ],
                recommendation="Take heap dump; check for unclosed connections, growing caches, or event listener leaks",
                confidence=88,
            ))

        report.metrics_analyzed["memory_samples"] = samples
        report.metrics_analyzed["growth_rate_mb_hr"] = round(growth_rate_mb_hr, 1)

    def _analyze_heap(self, service: str, report: SpecialistReport):
        heap = {
            "total_mb": 1024, "used_mb": 780, "free_mb": 244,
            "top_allocators": [
                {"class": "HashMap$Node", "count": 2500000, "size_mb": 190},
                {"class": "byte[]", "count": 800000, "size_mb": 150},
                {"class": "String", "count": 3200000, "size_mb": 120},
                {"class": "Connection", "count": 500, "size_mb": 45},
            ],
            "fragmentation_pct": 18,
        }

        usage_pct = (heap["used_mb"] / heap["total_mb"]) * 100
        if usage_pct > self.MEM_CRITICAL_PCT:
            sev = "critical"
        elif usage_pct > self.MEM_WARN_PCT:
            sev = "high"
        else:
            sev = "info"

        if sev != "info":
            report.findings.append(Finding(
                category="heap_usage",
                severity=sev,
                title=f"Heap utilization at {usage_pct:.0f}%",
                description=f"Used: {heap['used_mb']}MB / {heap['total_mb']}MB",
                evidence=[
                    f"Top allocator: {heap['top_allocators'][0]['class']} ({heap['top_allocators'][0]['size_mb']}MB)",
                    f"Fragmentation: {heap['fragmentation_pct']}%",
                ],
                recommendation="Increase heap size or optimize top allocators; check for object retention",
                confidence=90,
            ))

        if heap["fragmentation_pct"] > 25:
            report.findings.append(Finding(
                category="fragmentation", severity="medium",
                title=f"High heap fragmentation ({heap['fragmentation_pct']}%)",
                description="Memory fragmentation may cause allocation failures",
                recommendation="Consider compacting GC or service restart during maintenance window",
                confidence=75,
            ))

        report.metrics_analyzed["heap"] = heap

    def _check_gc_pressure(self, service: str, report: SpecialistReport):
        gc = {
            "gc_time_pct": 12, "gc_count_per_min": 45,
            "avg_pause_ms": 85, "max_pause_ms": 450,
            "collections": {"young": 40, "old": 5},
        }

        if gc["gc_time_pct"] > self.GC_PRESSURE_THRESHOLD:
            report.findings.append(Finding(
                category="gc_pressure", severity="high",
                title=f"High GC pressure ({gc['gc_time_pct']}% CPU time in GC)",
                description=f"GC running {gc['gc_count_per_min']} times/min, avg pause {gc['avg_pause_ms']}ms, max {gc['max_pause_ms']}ms",
                evidence=[
                    f"GC time: {gc['gc_time_pct']}% (threshold: {self.GC_PRESSURE_THRESHOLD}%)",
                    f"Old gen collections: {gc['collections']['old']}/min (high if >2)",
                ],
                recommendation="Increase heap size, tune GC parameters, or reduce allocation rate",
                confidence=85,
            ))

        if gc["max_pause_ms"] > 200:
            report.findings.append(Finding(
                category="gc_pause", severity="medium",
                title=f"Long GC pauses (max {gc['max_pause_ms']}ms)",
                description="GC pauses causing latency spikes",
                recommendation="Switch to low-pause GC (ZGC/Shenandoah) or reduce live object set",
                confidence=80,
            ))

        report.metrics_analyzed["gc"] = gc

    def _predict_oom(self, service: str, report: SpecialistReport):
        growth_rate = report.metrics_analyzed.get("growth_rate_mb_hr", 0)
        heap = report.metrics_analyzed.get("heap", {})
        free_mb = heap.get("free_mb", 500)

        if growth_rate > 0 and free_mb > 0:
            hours_until_oom = free_mb / growth_rate
            if hours_until_oom < 24:
                report.findings.append(Finding(
                    category="oom_prediction",
                    severity="critical" if hours_until_oom < 6 else "high",
                    title=f"OOM predicted in {hours_until_oom:.1f} hours",
                    description=f"At current growth rate ({growth_rate:.0f} MB/hr), {free_mb}MB free will be exhausted",
                    evidence=[
                        f"Growth rate: {growth_rate:.1f} MB/hr",
                        f"Free memory: {free_mb}MB",
                        f"Estimated OOM in: {hours_until_oom:.1f} hours",
                    ],
                    recommendation="Restart service to reclaim memory; investigate and fix root cause of leak",
                    confidence=82,
                ))

            report.metrics_analyzed["hours_until_oom"] = round(hours_until_oom, 1)
