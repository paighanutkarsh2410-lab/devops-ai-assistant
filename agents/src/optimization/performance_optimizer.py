"""
Agent Performance Optimizer: Parallel processing, caching, batch processing,
smart sampling, incremental processing, resource pooling, and benchmarking.
"""
import time
import logging
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


# ── TTL Cache ──────────────────────────────────────────────────────────

class TTLCache:
    """Thread-safe cache with TTL expiration."""

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: int = None):
        with self._lock:
            self._store[key] = (value, time.time() + (ttl or self._default_ttl))

    def invalidate(self, pattern: str = None):
        with self._lock:
            if pattern is None:
                self._store.clear()
            else:
                keys_to_remove = [k for k in self._store if pattern in k]
                for k in keys_to_remove:
                    del self._store[k]

    def cleanup(self):
        now = time.time()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
        return len(expired)

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(total, 1) * 100, 1),
        }


# ── Batch Processor ────────────────────────────────────────────────────

class BatchProcessor:
    """Collects items and processes them in batches."""

    def __init__(self, batch_size: int = 10, flush_interval_sec: float = 5.0):
        self._buffer: List[Any] = []
        self._lock = threading.Lock()
        self._batch_size = batch_size
        self._flush_interval = flush_interval_sec
        self._last_flush = time.time()
        self._total_batches = 0
        self._total_items = 0

    def add(self, item: Any) -> Optional[List[Any]]:
        """Add item to buffer. Returns batch if size threshold reached."""
        with self._lock:
            self._buffer.append(item)
            if len(self._buffer) >= self._batch_size:
                return self._flush()
        return None

    def flush(self) -> List[Any]:
        with self._lock:
            return self._flush()

    def _flush(self) -> List[Any]:
        batch = self._buffer[:]
        self._buffer.clear()
        self._last_flush = time.time()
        self._total_batches += 1
        self._total_items += len(batch)
        return batch

    def should_flush(self) -> bool:
        return (
            len(self._buffer) > 0
            and time.time() - self._last_flush > self._flush_interval
        )

    @property
    def stats(self) -> dict:
        return {
            "buffer_size": len(self._buffer),
            "total_batches": self._total_batches,
            "total_items": self._total_items,
            "avg_batch_size": round(self._total_items / max(self._total_batches, 1), 1),
        }


# ── Connection Pool ────────────────────────────────────────────────────

class ConnectionPool:
    """Generic connection pool with reuse."""

    def __init__(self, factory: Callable, max_size: int = 10):
        self._factory = factory
        self._max_size = max_size
        self._pool: List[Any] = []
        self._in_use: int = 0
        self._lock = threading.Lock()
        self._total_acquired = 0
        self._total_reused = 0

    def acquire(self) -> Any:
        with self._lock:
            self._total_acquired += 1
            if self._pool:
                self._total_reused += 1
                conn = self._pool.pop()
                self._in_use += 1
                return conn
            if self._in_use < self._max_size:
                self._in_use += 1
                return self._factory()
            raise RuntimeError("Connection pool exhausted")

    def release(self, conn: Any):
        with self._lock:
            self._in_use -= 1
            if len(self._pool) < self._max_size:
                self._pool.append(conn)

    @property
    def stats(self) -> dict:
        return {
            "pool_size": len(self._pool),
            "in_use": self._in_use,
            "max_size": self._max_size,
            "total_acquired": self._total_acquired,
            "reuse_rate": round(self._total_reused / max(self._total_acquired, 1) * 100, 1),
        }


# ── Incremental Processor ─────────────────────────────────────────────

class IncrementalProcessor:
    """Process only new data using checkpoints."""

    def __init__(self):
        self._checkpoints: Dict[str, Any] = {}
        self._processed_counts: Dict[str, int] = defaultdict(int)

    def get_checkpoint(self, key: str) -> Any:
        return self._checkpoints.get(key)

    def set_checkpoint(self, key: str, value: Any):
        self._checkpoints[key] = value

    def get_new_items(self, key: str, items: List[dict],
                      timestamp_field: str = "timestamp") -> List[dict]:
        """Return only items newer than the last checkpoint."""
        last = self._checkpoints.get(key)
        if last is None:
            self._checkpoints[key] = items[-1][timestamp_field] if items else None
            self._processed_counts[key] += len(items)
            return items

        new_items = [i for i in items if i.get(timestamp_field, "") > last]
        if new_items:
            self._checkpoints[key] = new_items[-1][timestamp_field]
            self._processed_counts[key] += len(new_items)
        return new_items

    @property
    def stats(self) -> dict:
        return {
            "checkpoints": len(self._checkpoints),
            "total_processed": dict(self._processed_counts),
        }


# ── Performance Benchmarker ────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    agent_name: str
    operation: str
    duration_ms: float
    items_processed: int
    throughput: float  # items/sec
    memory_delta_mb: float = 0
    target_met: bool = True
    target_ms: float = 0


# ── Main Optimizer Class ───────────────────────────────────────────────

# Performance targets (ms)
PERFORMANCE_TARGETS = {
    "monitor_agent_cycle": 30000,
    "diagnostic_agent_per_incident": 120000,
    "remediation_agent_total": 300000,
    "learning_agent_per_incident": 10000,
    "prediction_agent_per_forecast": 60000,
}


class AgentPerformanceOptimizer:
    """Centralizes all performance optimization strategies for agents."""

    def __init__(self, max_workers: int = 8):
        self.cache = TTLCache(default_ttl=300)
        self.llm_cache = TTLCache(default_ttl=600)  # LLM responses cached longer
        self.metric_cache = TTLCache(default_ttl=60)  # Metrics cached shorter

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.batch_processor = BatchProcessor(batch_size=10)
        self.incremental = IncrementalProcessor()

        self._benchmarks: List[BenchmarkResult] = []
        self._lock = threading.Lock()

    # ── Parallel Processing ────────────────────────────────────────────

    def run_parallel(self, tasks: List[Callable], timeout: int = 120) -> List[Any]:
        """Run independent tasks in parallel and collect results."""
        futures = {self._executor.submit(task): i for i, task in enumerate(tasks)}
        results = [None] * len(tasks)

        for future in as_completed(futures, timeout=timeout):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {"error": str(e)}
                logger.warning(f"[Optimizer] Parallel task {idx} failed: {e}")

        return results

    # ── Cached LLM Calls ───────────────────────────────────────────────

    def cached_llm_call(self, prompt: str, llm_fn: Callable,
                         ttl: int = 600) -> Any:
        """Cache LLM responses by prompt hash."""
        key = f"llm:{hashlib.md5(prompt.encode()).hexdigest()}"
        cached = self.llm_cache.get(key)
        if cached is not None:
            return cached
        result = llm_fn(prompt)
        self.llm_cache.set(key, result, ttl)
        return result

    # ── Smart Sampling ─────────────────────────────────────────────────

    @staticmethod
    def smart_sample(data: List[Any], max_size: int = 1000,
                     strategy: str = "reservoir") -> List[Any]:
        """Sample data while maintaining representativeness."""
        if len(data) <= max_size:
            return data

        if strategy == "reservoir":
            # Reservoir sampling — uniform random
            import random
            sample = data[:max_size]
            for i in range(max_size, len(data)):
                j = random.randint(0, i)
                if j < max_size:
                    sample[j] = data[i]
            return sample

        elif strategy == "stratified":
            # Take evenly spaced samples
            step = len(data) / max_size
            return [data[int(i * step)] for i in range(max_size)]

        elif strategy == "recent":
            # Take most recent + some older samples
            recent = data[-max_size // 2:]
            older_step = max(1, (len(data) - max_size // 2) // (max_size // 2))
            older = data[:len(data) - max_size // 2:older_step][:max_size // 2]
            return older + recent

        return data[:max_size]

    # ── Benchmarking ───────────────────────────────────────────────────

    def benchmark(self, agent_name: str, operation: str,
                  fn: Callable, items_count: int = 1) -> BenchmarkResult:
        """Benchmark an agent operation and track against targets."""
        start = time.time()
        fn()
        duration_ms = (time.time() - start) * 1000

        target_key = f"{agent_name}_{operation}".replace("-", "_").replace(" ", "_")
        target_ms = PERFORMANCE_TARGETS.get(target_key, 0)

        result = BenchmarkResult(
            agent_name=agent_name,
            operation=operation,
            duration_ms=round(duration_ms, 1),
            items_processed=items_count,
            throughput=round(items_count / (duration_ms / 1000) if duration_ms > 0 else 0, 1),
            target_met=duration_ms <= target_ms if target_ms > 0 else True,
            target_ms=target_ms,
        )

        with self._lock:
            self._benchmarks.append(result)

        return result

    def benchmark_agent_performance(self) -> dict:
        """Generate comprehensive performance report."""
        with self._lock:
            benchmarks = list(self._benchmarks)

        # Group by agent
        by_agent: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        for b in benchmarks:
            by_agent[b.agent_name].append(b)

        report = {
            "agents": {},
            "cache_stats": {
                "general": self.cache.stats,
                "llm": self.llm_cache.stats,
                "metrics": self.metric_cache.stats,
            },
            "batch_stats": self.batch_processor.stats,
            "incremental_stats": self.incremental.stats,
            "targets": PERFORMANCE_TARGETS,
        }

        for agent, results in by_agent.items():
            avg_duration = sum(r.duration_ms for r in results) / len(results)
            targets_met = sum(1 for r in results if r.target_met)

            report["agents"][agent] = {
                "total_operations": len(results),
                "avg_duration_ms": round(avg_duration, 1),
                "targets_met": targets_met,
                "targets_missed": len(results) - targets_met,
                "target_hit_rate": round(targets_met / len(results) * 100, 1),
                "operations": [
                    {
                        "operation": r.operation,
                        "duration_ms": r.duration_ms,
                        "throughput": r.throughput,
                        "target_met": r.target_met,
                    }
                    for r in results[-10:]  # Last 10
                ],
            }

        # Identify bottlenecks
        bottlenecks = []
        for b in benchmarks:
            if not b.target_met and b.target_ms > 0:
                overshoot = ((b.duration_ms - b.target_ms) / b.target_ms) * 100
                bottlenecks.append({
                    "agent": b.agent_name,
                    "operation": b.operation,
                    "duration_ms": b.duration_ms,
                    "target_ms": b.target_ms,
                    "overshoot_pct": round(overshoot, 1),
                })

        bottlenecks.sort(key=lambda x: -x["overshoot_pct"])
        report["bottlenecks"] = bottlenecks[:5]

        return report

    def cleanup_caches(self) -> dict:
        """Clean up expired entries from all caches."""
        cleaned = {
            "general": self.cache.cleanup(),
            "llm": self.llm_cache.cleanup(),
            "metrics": self.metric_cache.cleanup(),
        }
        return cleaned
