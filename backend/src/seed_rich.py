"""Rich demo seed - populates ALL tables for an impressive industry demo."""
import uuid, random, json
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = "postgresql://devops_user:yeNQKoPH4la2JqUZT4eoR5qssseFgEbC@dpg-d7gg1ka8qa3s73f61djg-a.oregon-postgres.render.com/devops_ai"
NOW = datetime.now(timezone.utc)
SERVICES = ['api-server', 'database', 'redis-cache', 'auth-service', 'payment-gateway', 'notification-service']
uid = lambda: str(uuid.uuid4())

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ─── Get user ───────────────────────────────────────────────────────
cur.execute("SELECT id FROM users WHERE email = 'aidevops@demo.com'")
row = cur.fetchone()
if not row:
    user_id = uid()
    hashed = "$2b$12$0DhFt17acDlUnDa194H3duGh2nYZW1urt4VRUnmlG0gf8szUnXype"
    cur.execute("INSERT INTO users (id, email, hashed_password, full_name, company, is_active, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (user_id, 'aidevops@demo.com', hashed, 'Utkarsh', 'SentryAI', True, NOW))
    print("Created user")
else:
    user_id = str(row[0])
    print(f"Using user: {user_id}")

# ─── Clear ALL old data ────────────────────────────────────────────
tables_to_clear = [
    'action_logs', 'action_outcomes', 'alerts', 'approval_requests',
    'predictive_alerts', 'incident_comments', 'log_entries', 'patterns',
    'learning_data', 'runbooks', 'workflows', 'escalation_policies',
    'maintenance_windows', 'chaos_experiments', 'notification_preferences',
    'forecasts', 'capacity_plans', 'cost_forecasts', 'workflow_executions',
    'runbook_executions', 'escalation_records', 'notification_logs',
]
for t in tables_to_clear:
    try:
        cur.execute(f"DELETE FROM {t}")
    except Exception:
        conn.rollback()
cur.execute("DELETE FROM metrics WHERE user_id = %s", (user_id,))
cur.execute("DELETE FROM deployments WHERE user_id = %s", (user_id,))
cur.execute("DELETE FROM incidents WHERE user_id = %s", (user_id,))
print("Cleared all old data")

# ─── INCIDENTS (55) ────────────────────────────────────────────────
incident_templates = [
    # 40 resolved
    ("API Response Time Degradation", "api-server", "high", "resolved", "P95 response time exceeded 2s threshold for 15 minutes", "Database connection pool exhaustion due to long-running queries", "Increased pool size from 10 to 25, optimized slow query on users table"),
    ("Memory Leak in Auth Service", "auth-service", "critical", "resolved", "Memory usage grew from 512MB to 3.8GB over 6 hours", "JWT token cache not evicting expired tokens", "Added TTL-based eviction policy, deployed hotfix v2.4.1"),
    ("Redis Cache Miss Rate Spike", "redis-cache", "medium", "resolved", "Cache miss rate jumped from 5% to 45%", "Key expiry misconfiguration after deployment v3.1.0", "Rolled back cache TTL config, added monitoring"),
    ("Database CPU at 95%", "database", "critical", "resolved", "PostgreSQL CPU sustained above 90% for 20 minutes", "Unindexed query on payments table scanning 2M rows", "Added composite index on (user_id, created_at)"),
    ("Payment Gateway Timeout", "payment-gateway", "critical", "resolved", "Payment success rate dropped to 62% from 99.8%", "Upstream provider rate limiting due to retry storm", "Implemented exponential backoff, added circuit breaker"),
    ("Notification Delivery Delay", "notification-service", "low", "resolved", "Email delivery delayed by 15-30 minutes", "Queue backlog from batch marketing job", "Separated marketing queue from transactional"),
    ("SSL Certificate Near Expiry", "api-server", "medium", "resolved", "Certificate expiring in 48 hours, auto-renewal failing", "Auto-renewal cron job DNS timeout", "Fixed DNS resolver config, renewed manually"),
    ("Disk Usage Critical on DB Server", "database", "high", "resolved", "Disk usage at 94%, risk of read-only mode", "WAL logs not being archived, growing at 2GB/hour", "Configured WAL archiving, added 100GB volume"),
    ("Auth Service 503 Errors", "auth-service", "high", "resolved", "12% of login requests returning 503", "LDAP dependency unreachable", "Made LDAP check non-blocking, added fallback"),
    ("API Rate Limiting Misconfigured", "api-server", "medium", "resolved", "Internal API calls being rate limited", "Rate limit set to 10 req/min instead of 1000", "Updated rate limit config for service accounts"),
    ("Redis Cluster Failover", "redis-cache", "high", "resolved", "30-second cache unavailability during failover", "Primary node OOM killed", "Increased memory limit, promoted replica"),
    ("CPU Spike on API Server", "api-server", "medium", "resolved", "CPU at 88% on 3 of 5 pods", "Regex catastrophic backtracking on input validation", "Replaced regex with optimized parser"),
    ("Database Connection Timeout", "database", "high", "resolved", "New connections failing with 'too many clients'", "Connection leak in background job processor", "Fixed connection leak, set idle timeout"),
    ("Payment Webhook Failures", "payment-gateway", "medium", "resolved", "43 failed webhook deliveries in last hour", "Schema mismatch after provider update", "Updated webhook handler, added versioning"),
    ("High Error Rate on /api/search", "api-server", "high", "resolved", "Search returning 500 for 8% of requests", "Elasticsearch 2 shards unassigned", "Rebalanced shards, fixed mapping conflict"),
    ("DNS Resolution Failures", "api-server", "critical", "resolved", "Intermittent DNS failures affecting 30% of outbound requests", "CoreDNS pod restarting due to memory limits", "Increased CoreDNS memory, added DNS caching layer"),
    ("Kafka Consumer Lag Spike", "notification-service", "high", "resolved", "Consumer lag reached 500k messages", "Consumer group rebalancing after pod restart", "Configured sticky partition assignment, added lag alerting"),
    ("GraphQL N+1 Query Detected", "api-server", "medium", "resolved", "GraphQL endpoint response times spiked to 8s", "DataLoader not batching nested user queries", "Implemented DataLoader batching, added query complexity limits"),
    ("Database Deadlock on Orders Table", "database", "high", "resolved", "Deadlock detected 15 times in 10 minutes on orders table", "Concurrent UPDATE on same rows from API and background jobs", "Reordered lock acquisition, added advisory locks"),
    ("Container Image Pull Failures", "auth-service", "medium", "resolved", "New pods failing to start: ErrImagePull", "Docker Hub rate limit exceeded on pull", "Migrated to private ECR registry, added image caching"),
    ("Memory OOM Kill on Worker Pods", "payment-gateway", "critical", "resolved", "3 worker pods OOM killed in 20 minutes", "Memory leak in PDF generation library", "Updated library version, added memory limits"),
    ("Load Balancer Health Check Flapping", "api-server", "low", "resolved", "ALB marking targets unhealthy intermittently", "Health check timeout too aggressive at 2s", "Increased timeout to 5s, added dedicated health endpoint"),
    ("Redis Sentinel Quorum Lost", "redis-cache", "critical", "resolved", "Redis sentinel lost quorum, no automatic failover possible", "2 of 3 sentinel nodes rescheduled to same host", "Added pod anti-affinity rules, restored quorum"),
    ("TLS Handshake Failures", "payment-gateway", "high", "resolved", "15% of outbound HTTPS calls failing TLS handshake", "Intermediate CA certificate expired", "Updated CA bundle, added certificate monitoring"),
    ("Kubernetes HPA Thrashing", "api-server", "medium", "resolved", "Pod count oscillating between 3 and 12 every 2 minutes", "CPU metric averaging window too short", "Increased stabilization window, adjusted scaling thresholds"),
    ("Postgres Vacuum Not Running", "database", "medium", "resolved", "Table bloat growing, query performance degrading", "autovacuum_max_workers exhausted by large tables", "Increased max workers, tuned vacuum cost settings"),
    ("Notification Service Circuit Breaker Open", "notification-service", "low", "resolved", "All notifications queued, none being sent", "SMTP relay returning 421 due to IP reputation", "Switched to backup SMTP relay, fixed SPF records"),
    ("API Gateway 502 Errors", "api-server", "high", "resolved", "5% of requests getting 502 Bad Gateway", "Upstream service taking >60s to respond, exceeding gateway timeout", "Increased timeout, added request queueing with backpressure"),
    ("Authentication Token Expiry Storm", "auth-service", "medium", "resolved", "Thousands of token refresh requests in 30-second window", "All tokens issued at same time during migration, expiring simultaneously", "Implemented jittered token expiry, rate-limited refresh endpoint"),
    ("Disk IOPS Throttled on Database", "database", "high", "resolved", "Query latency increased 10x due to IOPS throttling", "Burst IOPS credits exhausted on GP2 EBS volume", "Migrated to GP3 with provisioned IOPS"),
    ("Cross-AZ Network Latency Spike", "api-server", "low", "resolved", "P99 latency doubled for cross-AZ calls", "ISP peering issue between availability zones", "Added zone-aware routing, reduced cross-AZ traffic"),
    ("Payment Idempotency Violation", "payment-gateway", "critical", "resolved", "3 duplicate charges detected in 1 hour", "Race condition in idempotency key check", "Added distributed lock on idempotency key processing"),
    ("Elasticsearch Index Corruption", "api-server", "high", "resolved", "Search index returning stale results", "Disk full caused partial write to index shard", "Rebuilt index from source data, added disk space alerting"),
    ("gRPC Deadline Exceeded", "auth-service", "medium", "resolved", "25% of inter-service gRPC calls timing out", "Server-side garbage collection pauses exceeding deadline", "Tuned GC settings, increased client deadline"),
    ("Config Map Update Not Propagated", "notification-service", "low", "resolved", "Some pods using stale config after update", "Volume mount refresh delay, no pod restart triggered", "Added config hash annotation for automatic rollout"),
    ("Horizontal Pod Autoscaler Stuck", "payment-gateway", "medium", "resolved", "HPA reporting 'unable to fetch metrics' for 30 minutes", "Metrics server pod crashed due to OOM", "Increased metrics-server resources, added PDB"),
    ("Log Pipeline Backpressure", "api-server", "low", "resolved", "Log shipping delayed by 45 minutes", "Fluentd buffer overflow due to log volume spike", "Increased buffer size, added log sampling for debug level"),
    ("Service Mesh Sidecar Crash Loop", "auth-service", "high", "resolved", "Envoy sidecars crash-looping on 4 pods", "xDS configuration incompatible with sidecar version", "Rolled back mesh control plane, updated sidecar injection"),
    ("Database Replication Lag: 30s", "database", "critical", "resolved", "Read replica lagging 30 seconds behind primary", "Long-running transaction blocking WAL apply", "Terminated long transaction, added statement timeout"),
    ("CDN Cache Purge Failure", "api-server", "low", "resolved", "Static assets serving stale content after deploy", "CDN API rate limit hit during mass purge", "Implemented incremental cache invalidation"),
    # 10 open/investigating
    ("Memory Pressure on Cache Nodes", "redis-cache", "medium", "investigating", "Memory usage at 82%, approaching eviction threshold", None, None),
    ("Notification Email Bounces", "notification-service", "medium", "open", "18% bounce rate on transactional emails, SPF alignment issues", None, None),
    ("Auth Token Validation Slow", "auth-service", "high", "investigating", "Token validation adding 350ms to every authenticated request", None, None),
    ("Cascading Failure: API to DB to Cache", "api-server", "critical", "open", "Multi-service degradation affecting 60% of requests", None, None),
    ("Deployment Rollback: v3.2.0", "api-server", "high", "investigating", "Error rate jumped to 25% within 2 minutes of deployment", None, None),
    ("Database Query Plan Regression", "database", "medium", "investigating", "Query planner choosing sequential scan over index after ANALYZE", None, None),
    ("Payment Processing Latency", "payment-gateway", "high", "open", "P99 payment processing time at 4.2s, normally under 800ms", None, None),
    ("Redis Memory Fragmentation", "redis-cache", "low", "investigating", "Memory fragmentation ratio at 1.8, causing OOM despite available memory", None, None),
    ("API Server Pod Evictions", "api-server", "medium", "open", "3 pods evicted in last hour due to node memory pressure", None, None),
    ("Certificate Rotation Failing", "auth-service", "high", "open", "mTLS certificate rotation failing, certs expire in 12 hours", None, None),
    # 5 acknowledged
    ("Slow Query Alert: user_sessions", "database", "medium", "acknowledged", "SELECT on user_sessions taking >5s, missing index on session_token", None, None),
    ("Notification Queue Depth Growing", "notification-service", "low", "acknowledged", "Queue depth at 15k messages, normally under 1k", None, None),
    ("API Rate Limit Exceeded by Partner", "api-server", "low", "acknowledged", "Partner integration exceeding 10k req/min rate limit", None, None),
    ("Container Registry Disk Full", "auth-service", "medium", "acknowledged", "Private registry at 95% disk capacity", None, None),
    ("Flaky Health Check on Worker", "payment-gateway", "low", "acknowledged", "Health check failing intermittently every ~5 minutes", None, None),
]

incident_ids = []
incident_rows = []
for title, service, severity, status, desc, root_cause, solution in incident_templates:
    inc_id = uid()
    incident_ids.append(inc_id)
    hours_ago = random.randint(1, 720)
    detected = NOW - timedelta(hours=hours_ago)
    is_resolved = status == "resolved"
    is_auto = is_resolved and random.random() < 0.4
    res_secs = random.randint(60, 3600) if is_resolved else None
    resolved_at = detected + timedelta(seconds=res_secs) if is_resolved else None
    incident_rows.append((inc_id, user_id, title, desc, severity, status, service,
                          root_cause, solution, detected, resolved_at, is_auto, res_secs, detected))

execute_values(cur, """
    INSERT INTO incidents (id, user_id, title, description, severity, status, service_name,
        root_cause, solution, detected_at, resolved_at, auto_resolved, resolution_time_seconds, created_at)
    VALUES %s
""", incident_rows)
print(f"Created {len(incident_rows)} incidents")

# ─── METRICS (5000+) ──────────────────────────────────────────────
metric_rows = []
for service in SERVICES:
    for metric_name in ['cpu_percent', 'memory_percent', 'response_time_ms', 'error_rate', 'request_count']:
        base = {'cpu_percent': 35, 'memory_percent': 55, 'response_time_ms': 120, 'error_rate': 1.5, 'request_count': 500}[metric_name]
        unit = {'cpu_percent': '%', 'memory_percent': '%', 'response_time_ms': 'ms', 'error_rate': '%', 'request_count': 'req/s'}[metric_name]
        for hours in range(0, 336, 1):  # 14 days, every hour
            ts = NOW - timedelta(hours=hours)
            noise = random.gauss(0, base * 0.15)
            hour_factor = 1 + 0.3 * abs(ts.hour - 14) / 14
            # Inject some anomalies
            anomaly = 0
            if random.random() < 0.02:
                anomaly = base * random.uniform(0.5, 1.5)
            val = max(0.1, base * hour_factor + noise + anomaly)
            metric_rows.append((uid(), user_id, service, metric_name, round(val, 2), unit, ts))

execute_values(cur, """
    INSERT INTO metrics (id, user_id, service_name, metric_name, value, unit, timestamp)
    VALUES %s
""", metric_rows, page_size=500)
print(f"Created {len(metric_rows)} metrics")

# ─── ALERTS (35) ──────────────────────────────────────────────────
alert_templates = [
    ("CPU usage above 80%", "api-server", "api-server CPU at 87% for 5 minutes", "warning"),
    ("Memory critical: 92%", "auth-service", "auth-service memory approaching OOM limit", "critical"),
    ("Response time degraded", "api-server", "P95 response time at 1.8s (threshold: 1s)", "warning"),
    ("Disk usage warning", "database", "database disk at 85% capacity", "warning"),
    ("Error rate spike", "api-server", "api-server error rate at 5.2% (threshold: 2%)", "critical"),
    ("Connection pool exhausted", "database", "database connections at 98/100", "critical"),
    ("Cache hit rate low", "redis-cache", "redis cache hit rate dropped to 60%", "info"),
    ("SSL certificate expiry", "api-server", "api-server cert expires in 7 days", "info"),
    ("Pod restart detected", "payment-gateway", "payment-gateway pod restarted 3 times in 10 min", "warning"),
    ("Database replication lag", "database", "replica lagging 15 seconds behind primary", "warning"),
    ("Network packet loss", "api-server", "0.5% packet loss on eth0 interface", "info"),
    ("Kafka consumer lag", "notification-service", "consumer lag at 100k messages", "warning"),
    ("Memory leak detected", "auth-service", "memory growing linearly, OOM in ~4 hours", "critical"),
    ("API 5xx rate elevated", "api-server", "5xx error rate at 3.1%, threshold 1%", "critical"),
    ("Queue depth critical", "notification-service", "notification queue at 25k messages", "warning"),
    ("Database locks detected", "database", "12 active lock waits on orders table", "warning"),
    ("DNS resolution slow", "api-server", "DNS queries taking >500ms average", "info"),
    ("Container OOM killed", "payment-gateway", "worker-3 OOM killed at 2.1GB", "critical"),
    ("TLS cert expiring soon", "payment-gateway", "mTLS cert expires in 48 hours", "warning"),
    ("Deployment health check failing", "auth-service", "new deployment failing readiness probe", "critical"),
    ("Log volume spike", "api-server", "log ingestion at 50k/s, 5x normal", "info"),
    ("Redis memory fragmentation", "redis-cache", "fragmentation ratio at 1.6", "warning"),
    ("Service mesh latency", "auth-service", "sidecar proxy adding 50ms per hop", "info"),
    ("Horizontal scaling triggered", "api-server", "auto-scaling from 5 to 12 pods", "info"),
    ("Payment timeout rate", "payment-gateway", "8% of payments timing out", "critical"),
    ("Backup job failed", "database", "nightly backup failed after 2 hours", "warning"),
    ("CDN origin errors", "api-server", "CDN reporting 5% origin error rate", "warning"),
    ("Rate limit approaching", "api-server", "partner API at 80% of rate limit", "info"),
    ("Health check flapping", "payment-gateway", "health check alternating pass/fail", "warning"),
    ("Disk IOPS saturated", "database", "disk IOPS at 95% of provisioned limit", "warning"),
    ("Memory swap detected", "redis-cache", "redis using 256MB of swap space", "critical"),
    ("Network policy violation", "auth-service", "unexpected traffic from unknown CIDR", "critical"),
    ("Cron job overrun", "notification-service", "cleanup job running for 4 hours", "warning"),
    ("Config drift detected", "api-server", "live config differs from declared state", "info"),
    ("Graceful shutdown timeout", "payment-gateway", "pod taking >30s to terminate", "warning"),
]

alert_rows = []
for j, (title, svc, msg, sev) in enumerate(alert_templates):
    hours_ago = random.randint(1, 168)
    triggered = NOW - timedelta(hours=hours_ago)
    ack = j < 25
    res = j < 18
    inc_id = incident_ids[j % len(incident_ids)] if j < 20 else None
    alert_rows.append((uid(), user_id, inc_id, title, msg, sev, ack, res, triggered,
                       triggered + timedelta(minutes=random.randint(5, 60)) if ack else None,
                       triggered + timedelta(hours=random.randint(1, 4)) if res else None))

execute_values(cur, """
    INSERT INTO alerts (id, user_id, incident_id, title, message, severity,
        acknowledged, resolved, triggered_at, acknowledged_at, resolved_at)
    VALUES %s
""", alert_rows)
print(f"Created {len(alert_rows)} alerts")

# ─── ACTION LOGS (30) ─────────────────────────────────────────────
action_names = ["restart_service", "scale_up", "scale_down", "clear_cache", "rollback_deployment",
                "increase_resources", "kill_process", "rate_limit_adjust", "flush_connections",
                "rotate_credentials", "apply_patch", "drain_node", "failover_primary"]
action_rows = []
for i in range(30):
    name = random.choice(action_names)
    svc = random.choice(SERVICES)
    status = random.choices(["success", "failure", "rollback"], weights=[75, 15, 10])[0]
    dur = round(random.uniform(1.5, 120), 1)
    action_rows.append((uid(), incident_ids[i % len(incident_ids)], name, "remediation",
                        "remediation-agent", NOW - timedelta(hours=random.randint(1, 400)),
                        dur, status, round(random.uniform(0.2, 0.98), 2), status == "rollback",
                        name in ["rollback_deployment", "increase_resources", "failover_primary"],
                        "admin@devops-ai.system" if status == "rollback" else None))

execute_values(cur, """
    INSERT INTO action_logs (id, incident_id, action_name, action_type, executed_by,
        executed_at, duration_seconds, status, impact_score, rollback_performed,
        approval_required, approved_by)
    VALUES %s
""", action_rows)
print(f"Created {len(action_rows)} action logs")

# ─── DEPLOYMENTS (25) ─────────────────────────────────────────────
deploy_rows = []
versions = {}
for i in range(25):
    svc = SERVICES[i % len(SERVICES)]
    if svc not in versions:
        versions[svc] = [3, 0, 0]
    v = versions[svc]
    ver = f"v{v[0]}.{v[1]}.{v[2]}"
    v[2] += 1
    if v[2] > 5:
        v[2] = 0; v[1] += 1
    commit = ''.join(random.choices('abcdef0123456789', k=7))
    status = random.choices(["success", "success", "success", "failed", "rolled_back"], weights=[60, 20, 10, 5, 5])[0]
    deploy_rows.append((uid(), user_id, svc, ver, commit, random.choice(["github-actions", "argocd", "manual"]),
                        NOW - timedelta(days=i + random.random()), f"Production deploy {ver} - {svc}"))

execute_values(cur, """
    INSERT INTO deployments (id, user_id, service_name, version, commit_hash,
        deployed_by, deployed_at, description)
    VALUES %s
""", deploy_rows)
print(f"Created {len(deploy_rows)} deployments")

# ─── PATTERNS (12) ────────────────────────────────────────────────
pattern_rows = []
patterns_data = [
    ("Memory Leak Pattern", "Gradual memory increase leading to OOM", "resource_exhaustion", 23, 0.89,
     ["increasing_memory", "gc_pressure", "response_degradation"], ["unbounded_cache", "connection_leak"], ["restart", "increase_limits"]),
    ("CPU Spike Pattern", "Sudden CPU increase from inefficient queries", "performance", 31, 0.92,
     ["high_cpu", "slow_queries", "increased_latency"], ["unindexed_query", "regex_backtracking"], ["add_index", "optimize_query"]),
    ("Connection Pool Exhaustion", "All connections consumed, new requests fail", "resource_exhaustion", 15, 0.85,
     ["connection_timeout", "503_errors", "queue_buildup"], ["connection_leak", "pool_too_small"], ["increase_pool", "fix_leak"]),
    ("Cascading Failure", "One service failure causing downstream failures", "availability", 8, 0.78,
     ["multi_service_errors", "timeout_cascade", "circuit_breaker_open"], ["no_circuit_breaker", "tight_coupling"], ["add_circuit_breaker", "bulkhead"]),
    ("Deployment Regression", "Performance degradation after new deployment", "deployment", 18, 0.91,
     ["error_rate_increase", "latency_spike", "post_deploy"], ["code_regression", "config_change"], ["rollback", "hotfix"]),
    ("Cache Stampede", "Mass cache expiry causing DB overload", "performance", 6, 0.82,
     ["cache_miss_spike", "db_cpu_spike", "response_timeout"], ["synchronized_expiry", "no_jitter"], ["add_jitter", "warm_cache"]),
    ("Disk Space Exhaustion", "Disk usage growing until critical threshold", "resource_exhaustion", 12, 0.94,
     ["disk_usage_growing", "write_errors", "service_degradation"], ["log_rotation_failure", "temp_file_accumulation"], ["cleanup", "expand_volume"]),
    ("Network Partition", "Intermittent network connectivity issues", "availability", 5, 0.71,
     ["packet_loss", "connection_reset", "dns_failures"], ["isp_issue", "firewall_change"], ["failover", "add_redundancy"]),
    ("Certificate Expiry", "TLS certificates approaching expiration", "security", 9, 0.97,
     ["tls_errors", "renewal_failure", "expiry_warning"], ["auto_renewal_broken", "dns_timeout"], ["manual_renewal", "fix_automation"]),
    ("Rate Limit Breach", "API rate limits exceeded by clients", "traffic", 20, 0.88,
     ["429_responses", "client_errors", "queue_buildup"], ["traffic_spike", "misconfigured_client"], ["adjust_limits", "throttle"]),
    ("GC Pause Impact", "Long garbage collection pauses affecting latency", "performance", 14, 0.84,
     ["p99_spikes", "gc_pause_duration", "cpu_spikes"], ["heap_too_large", "object_churn"], ["tune_gc", "reduce_allocation"]),
    ("Log Volume Anomaly", "Unusual increase in log output volume", "observability", 11, 0.76,
     ["log_rate_increase", "disk_pressure", "pipeline_lag"], ["debug_logging_enabled", "error_loop"], ["reduce_log_level", "fix_error"]),
]
for name, desc, ptype, freq, conf, symptoms, causes, actions_list in patterns_data:
    trend = random.choice(["up", "down", "stable"])
    last_seen = NOW - timedelta(hours=random.randint(1, 72))
    pattern_rows.append((uid(), name, desc, ptype, freq, conf,
                         json.dumps(symptoms), json.dumps(causes), json.dumps(actions_list),
                         json.dumps(random.sample(SERVICES, random.randint(1, 3))),
                         json.dumps({"peak_hours": [9, 10, 14, 15], "off_peak": [2, 3, 4]}),
                         trend, last_seen, NOW - timedelta(days=random.randint(1, 30)), NOW))

execute_values(cur, """
    INSERT INTO patterns (id, name, description, pattern_type, frequency, confidence,
        symptoms, common_root_causes, best_actions, affected_services, time_distribution,
        trending, last_seen, created_at, updated_at)
    VALUES %s
""", pattern_rows)
print(f"Created {len(pattern_rows)} patterns")

# ─── LEARNING DATA (20) ──────────────────────────────────────────
learning_rows = []
for svc in SERVICES:
    for action in random.sample(["restart_service", "scale_up", "clear_cache", "rollback_deployment", "increase_resources", "flush_connections"], 3):
        total = random.randint(20, 150)
        successes = int(total * random.uniform(0.6, 0.98))
        learning_rows.append((uid(), random.choice(["resource_exhaustion", "performance", "availability"]),
                             svc, action, random.randint(5, 40),
                             round(successes / total * 100, 1), total, successes,
                             round(random.uniform(30, 600), 1), round(random.uniform(0.6, 0.98), 2),
                             json.dumps(["high_cpu", "memory_pressure", "error_rate_increase"]),
                             json.dumps(["resource_limit", "code_regression", "config_change"]),
                             json.dumps(["restart", "scale_up", "rollback"]),
                             NOW - timedelta(hours=random.randint(1, 168)), NOW - timedelta(days=random.randint(5, 30)), NOW))

execute_values(cur, """
    INSERT INTO learning_data (id, pattern_type, service_name, action_name, frequency,
        success_rate, total_attempts, total_successes, avg_resolution_time, confidence,
        symptoms, root_causes, solutions, last_seen, created_at, updated_at)
    VALUES %s
""", learning_rows)
print(f"Created {len(learning_rows)} learning data entries")

# ─── APPROVAL REQUESTS (10) ──────────────────────────────────────
approval_rows = []
approval_actions = [
    ("rollback_deployment", "Rollback api-server to v3.1.2 due to error rate spike", "high"),
    ("scale_up", "Scale payment-gateway from 3 to 8 replicas", "medium"),
    ("increase_resources", "Increase database memory from 4GB to 8GB", "high"),
    ("failover_primary", "Failover database to replica in us-east-1b", "critical"),
    ("rotate_credentials", "Rotate API keys for payment-gateway integration", "high"),
    ("drain_node", "Drain node worker-5 for maintenance", "medium"),
    ("apply_patch", "Apply security patch CVE-2024-1234 to auth-service", "high"),
    ("restart_service", "Restart notification-service to clear queue backlog", "low"),
    ("clear_cache", "Flush entire Redis cache to resolve stale data", "medium"),
    ("scale_down", "Scale down api-server from 12 to 5 pods post-peak", "low"),
]
for i, (action, desc, risk) in enumerate(approval_actions):
    requested_at = NOW - timedelta(hours=random.randint(1, 72))
    if i < 4:
        status = "pending"
        approved_by = None
        approved_at = None
    elif i < 7:
        status = "approved"
        approved_by = "admin@devops-ai.system"
        approved_at = requested_at + timedelta(minutes=random.randint(2, 30))
    else:
        status = "rejected"
        approved_by = "admin@devops-ai.system"
        approved_at = requested_at + timedelta(minutes=random.randint(5, 60))
    approval_rows.append((uid(), incident_ids[i], action, desc, risk, "remediation-agent",
                          requested_at, status, approved_by, approved_at, 60))

execute_values(cur, """
    INSERT INTO approval_requests (id, incident_id, action_name, action_description, risk_level,
        requested_by, requested_at, status, approved_by, approved_at, expiry_minutes)
    VALUES %s
""", approval_rows)
print(f"Created {len(approval_rows)} approval requests (4 pending)")

# ─── PREDICTIVE ALERTS (15) ──────────────────────────────────────
pred_rows = []
pred_data = [
    ("CPU Threshold Breach Predicted", "api-server CPU will exceed 90% within 6 hours", "warning", "threshold_breach", "api-server", "cpu_percent", 0.87, 6),
    ("Memory Exhaustion Forecast", "auth-service will OOM within 12 hours at current growth rate", "critical", "resource_exhaustion", "auth-service", "memory_percent", 0.92, 12),
    ("Disk Full in 48 Hours", "database disk will reach 100% based on WAL growth", "warning", "capacity", "database", "disk_percent", 0.85, 48),
    ("Response Time SLA Breach", "api-server P95 will exceed SLA target within 3 hours", "critical", "sla_violation", "api-server", "response_time_ms", 0.79, 3),
    ("Cache Eviction Storm Expected", "redis memory at 85%, mass eviction imminent", "warning", "resource_exhaustion", "redis-cache", "memory_percent", 0.83, 8),
    ("Payment Failure Rate Rising", "payment success rate trending below 99% threshold", "critical", "threshold_breach", "payment-gateway", "error_rate", 0.88, 4),
    ("Connection Pool Saturation", "database connections growing, will exhaust pool in 2 hours", "warning", "resource_exhaustion", "database", "connection_count", 0.91, 2),
    ("Traffic Surge Predicted", "Based on historical patterns, 3x traffic surge expected at 14:00", "info", "capacity", "api-server", "request_count", 0.94, 5),
    ("Certificate Expiry: 7 Days", "payment-gateway mTLS certificate expires in 7 days", "info", "security", "payment-gateway", None, 0.99, 168),
    ("Notification Queue Overflow", "Queue depth growing at 1k/min, will overflow in 4 hours", "warning", "capacity", "notification-service", "queue_depth", 0.81, 4),
    ("Database Replication Lag Growing", "Replica lag increasing 2s/hour, will exceed threshold", "warning", "threshold_breach", "database", "replication_lag", 0.86, 10),
    ("Memory Leak Pattern Detected", "auth-service showing linear memory growth consistent with leak", "critical", "anomaly", "auth-service", "memory_percent", 0.93, 8),
    ("IOPS Limit Approaching", "database IOPS at 80% of provisioned limit during peak", "info", "capacity", "database", "iops", 0.77, 24),
    ("Error Rate Anomaly", "api-server error rate 3 std deviations above normal", "warning", "anomaly", "api-server", "error_rate", 0.84, 2),
    ("Pod Scheduling Risk", "Node resources at 85%, new pods may fail to schedule", "info", "capacity", "api-server", "node_capacity", 0.72, 12),
]
for title, msg, sev, ptype, svc, metric, conf, hours_until in pred_data:
    prevented = random.random() < 0.4
    pred_rows.append((uid(), title, msg, sev, ptype, svc, metric, conf,
                      NOW + timedelta(hours=hours_until), hours_until, prevented,
                      "auto-remediation" if prevented else None,
                      NOW - timedelta(hours=random.randint(0, 2)) if prevented else None,
                      json.dumps(["scale_up", "increase_limits", "alert_oncall"]),
                      NOW - timedelta(hours=random.randint(0, 24))))

execute_values(cur, """
    INSERT INTO predictive_alerts (id, title, message, severity, prediction_type, service_name,
        metric_name, confidence, forecasted_date, hours_until_issue, prevented, prevention_action,
        prevented_at, preventive_actions, created_at)
    VALUES %s
""", pred_rows)
print(f"Created {len(pred_rows)} predictive alerts")

# ─── LOG ENTRIES (200) ────────────────────────────────────────────
log_templates = [
    ("INFO", "Request processed successfully in {ms}ms"),
    ("INFO", "Health check passed - all dependencies healthy"),
    ("WARN", "Response time above threshold: {ms}ms > 1000ms"),
    ("WARN", "Connection pool utilization at {pct}%"),
    ("ERROR", "Failed to connect to upstream service: connection refused"),
    ("ERROR", "Unhandled exception in request handler: NullPointerException"),
    ("ERROR", "Database query timeout after 30s: SELECT * FROM large_table"),
    ("INFO", "Deployment {ver} started for {svc}"),
    ("INFO", "Auto-scaling triggered: {from_pods} -> {to_pods} pods"),
    ("WARN", "Rate limit approaching: {pct}% of limit used"),
    ("ERROR", "Circuit breaker opened for {svc} after 5 consecutive failures"),
    ("INFO", "Cache warmed successfully: {count} keys loaded"),
    ("WARN", "Disk usage at {pct}% on /data volume"),
    ("ERROR", "TLS handshake failed: certificate expired"),
    ("INFO", "Garbage collection completed in {ms}ms, freed {mb}MB"),
]
log_rows = []
for _ in range(200):
    svc = random.choice(SERVICES)
    level, template = random.choice(log_templates)
    msg = template.format(ms=random.randint(50, 5000), pct=random.randint(50, 99),
                          ver=f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                          svc=random.choice(SERVICES), from_pods=random.randint(3, 5),
                          to_pods=random.randint(6, 15), count=random.randint(100, 50000),
                          mb=random.randint(50, 500))
    ts = NOW - timedelta(hours=random.randint(0, 168))
    log_rows.append((uid(), user_id, svc, level, msg, ts, json.dumps({"request_id": uid()[:8]})))

execute_values(cur, """
    INSERT INTO log_entries (id, user_id, service_name, level, message, timestamp, metadata)
    VALUES %s
""", log_rows)
print(f"Created {len(log_rows)} log entries")

# ─── INCIDENT COMMENTS (40) ──────────────────────────────────────
comment_texts = [
    "Investigating - initial triage shows this is related to the recent deployment",
    "Confirmed root cause. Working on fix now.",
    "Applied temporary mitigation. Error rate dropping.",
    "Fix deployed to staging, testing now.",
    "Fix verified in staging. Rolling out to production.",
    "Production deployment complete. Monitoring metrics.",
    "Metrics stabilized. Marking as resolved.",
    "Adding this to our post-incident review backlog.",
    "Similar issue occurred last month - see INC-234. Same root cause.",
    "Escalated to database team for review.",
    "Customer impact confirmed: ~200 users affected during the window.",
    "Runbook updated with new remediation steps.",
    "Auto-remediation kicked in and restarted the service.",
    "This was caught by our new predictive alerting - 2 hours before customer impact.",
    "Rolling back deployment as a precaution while we investigate.",
]
comment_rows = []
for _ in range(40):
    inc_id = random.choice(incident_ids[:30])
    comment_rows.append((uid(), inc_id, user_id, random.choice(comment_texts),
                         None, NOW - timedelta(hours=random.randint(0, 200)), None))

execute_values(cur, """
    INSERT INTO incident_comments (id, incident_id, user_id, comment_text, attachments, created_at, edited_at)
    VALUES %s
""", comment_rows)
print(f"Created {len(comment_rows)} incident comments")

# ─── ACTION OUTCOMES (50) ────────────────────────────────────────
outcome_rows = []
for _ in range(50):
    success = random.random() < 0.78
    outcome_rows.append((uid(), random.choice(incident_ids[:40]),
                         random.choice(["restart_service", "scale_up", "clear_cache", "rollback_deployment", "increase_resources"]),
                         random.choice(["resource_exhaustion", "performance", "availability", "deployment"]),
                         random.choice(SERVICES), success, round(random.uniform(5, 300), 1),
                         round(random.uniform(0.2, 0.98), 2), random.random() < 0.6,
                         random.randint(1, 5) if random.random() < 0.6 else None,
                         NOW - timedelta(hours=random.randint(1, 500))))

execute_values(cur, """
    INSERT INTO action_outcomes (id, incident_id, action_name, incident_pattern, service_name,
        success, duration_seconds, impact_score, was_recommended, recommendation_rank, timestamp)
    VALUES %s
""", outcome_rows)
print(f"Created {len(outcome_rows)} action outcomes")

# ─── RUNBOOKS (8) ────────────────────────────────────────────────
runbook_rows = []
runbooks_data = [
    ("High CPU Remediation", "Steps to diagnose and resolve high CPU usage", "high_cpu", "api-server", "high",
     [{"step": 1, "action": "Check top processes", "command": "kubectl top pods -n production"},
      {"step": 2, "action": "Check for slow queries", "command": "SELECT * FROM pg_stat_activity WHERE state='active'"},
      {"step": 3, "action": "Scale up if needed", "command": "kubectl scale deployment api-server --replicas=8"},
      {"step": 4, "action": "Monitor metrics for 10 minutes"}], 15),
    ("Memory Leak Investigation", "Diagnose and mitigate memory leaks", "memory_leak", "auth-service", "critical",
     [{"step": 1, "action": "Capture heap dump", "command": "jmap -dump:format=b,file=/tmp/heapdump.hprof PID"},
      {"step": 2, "action": "Check GC logs", "command": "kubectl logs auth-service --tail=1000 | grep GC"},
      {"step": 3, "action": "Restart affected pods", "command": "kubectl rollout restart deployment/auth-service"},
      {"step": 4, "action": "Apply memory limits if not set"}], 30),
    ("Database Failover", "Execute database primary failover", "db_failover", "database", "critical",
     [{"step": 1, "action": "Verify replica health", "command": "SELECT * FROM pg_stat_replication"},
      {"step": 2, "action": "Promote replica", "command": "pg_ctl promote -D /var/lib/postgresql/data"},
      {"step": 3, "action": "Update connection strings"},
      {"step": 4, "action": "Verify application connectivity"},
      {"step": 5, "action": "Monitor for 30 minutes"}], 45),
    ("Cache Flush Procedure", "Safely flush and warm cache", "cache_issues", "redis-cache", "medium",
     [{"step": 1, "action": "Check cache stats", "command": "redis-cli INFO memory"},
      {"step": 2, "action": "Flush stale keys", "command": "redis-cli FLUSHDB ASYNC"},
      {"step": 3, "action": "Warm critical paths", "command": "python warm_cache.py --critical-only"},
      {"step": 4, "action": "Verify hit rate recovering"}], 20),
    ("Deployment Rollback", "Emergency rollback procedure", "deployment_failure", "api-server", "high",
     [{"step": 1, "action": "Identify last stable version", "command": "kubectl rollout history deployment/api-server"},
      {"step": 2, "action": "Execute rollback", "command": "kubectl rollout undo deployment/api-server"},
      {"step": 3, "action": "Verify pods healthy", "command": "kubectl get pods -l app=api-server"},
      {"step": 4, "action": "Check error rates returning to baseline"}], 10),
    ("SSL Certificate Renewal", "Manual certificate renewal steps", "cert_expiry", "api-server", "medium",
     [{"step": 1, "action": "Generate new CSR", "command": "openssl req -new -key server.key -out server.csr"},
      {"step": 2, "action": "Submit to CA and retrieve cert"},
      {"step": 3, "action": "Deploy new certificate", "command": "kubectl create secret tls --cert=cert.pem --key=key.pem"},
      {"step": 4, "action": "Verify TLS handshake", "command": "openssl s_client -connect api.example.com:443"}], 25),
    ("Network Troubleshooting", "Debug network connectivity issues", "network_issues", None, "medium",
     [{"step": 1, "action": "Check DNS resolution", "command": "nslookup service.namespace.svc.cluster.local"},
      {"step": 2, "action": "Test connectivity", "command": "curl -v http://service:8080/health"},
      {"step": 3, "action": "Check network policies", "command": "kubectl get networkpolicies -n production"},
      {"step": 4, "action": "Review service mesh config"}], 20),
    ("Incident Response", "General incident response procedure", None, None, "critical",
     [{"step": 1, "action": "Acknowledge alert and assess severity"},
      {"step": 2, "action": "Open incident channel", "command": "Create #inc-YYYYMMDD Slack channel"},
      {"step": 3, "action": "Identify affected services and blast radius"},
      {"step": 4, "action": "Apply immediate mitigation"},
      {"step": 5, "action": "Communicate status to stakeholders"},
      {"step": 6, "action": "Resolve and document root cause"},
      {"step": 7, "action": "Schedule post-incident review"}], 60),
]
for name, desc, pattern, svc, sev, steps, duration in runbooks_data:
    runbook_rows.append((uid(), user_id, name, desc, pattern, svc, sev,
                         json.dumps(steps), duration, 1, None,
                         json.dumps(["production", "remediation"]),
                         NOW - timedelta(days=random.randint(5, 30)), NOW))

execute_values(cur, """
    INSERT INTO runbooks (id, user_id, name, description, incident_pattern, service_name, severity,
        steps, estimated_duration_minutes, version, previous_versions, tags, created_at, updated_at)
    VALUES %s
""", runbook_rows)
print(f"Created {len(runbook_rows)} runbooks")

# ─── WORKFLOWS (6) ───────────────────────────────────────────────
workflow_rows = []
workflows_data = [
    ("Auto-Scale on High CPU", "Automatically scale up when CPU exceeds threshold",
     {"metric": "cpu_percent", "operator": ">", "threshold": 80, "duration_minutes": 5},
     [{"action": "scale_up", "params": {"increment": 2}}, {"action": "notify", "channel": "slack"}], True),
    ("Cache Flush on Miss Rate", "Clear cache when miss rate is too high",
     {"metric": "cache_miss_rate", "operator": ">", "threshold": 30, "service": "redis-cache"},
     [{"action": "clear_cache"}, {"action": "warm_cache"}], True),
    ("Auto-Rollback on Error Spike", "Rollback deployment when error rate spikes",
     {"metric": "error_rate", "operator": ">", "threshold": 5, "after_deployment": True},
     [{"action": "rollback_deployment"}, {"action": "notify", "channel": "pagerduty"}], True),
    ("Nightly DB Maintenance", "Run vacuum and analyze on large tables",
     {"schedule": "0 3 * * *", "type": "cron"},
     [{"action": "run_vacuum"}, {"action": "run_analyze"}, {"action": "log_stats"}], True),
    ("Incident Auto-Escalation", "Escalate unacknowledged critical incidents",
     {"severity": "critical", "unacknowledged_minutes": 10},
     [{"action": "escalate", "to": "oncall-primary"}, {"action": "notify", "channel": "pagerduty"}], True),
    ("Cost Alert Workflow", "Alert when daily cost exceeds budget",
     {"metric": "daily_cost", "operator": ">", "threshold": 500},
     [{"action": "notify", "channel": "slack"}, {"action": "generate_report"}], False),
]
for name, desc, triggers, steps, enabled in workflows_data:
    workflow_rows.append((uid(), user_id, name, desc, json.dumps(triggers), json.dumps(steps),
                          enabled, NOW - timedelta(days=random.randint(5, 30)), NOW))

execute_values(cur, """
    INSERT INTO workflows (id, user_id, name, description, trigger_conditions, steps, enabled, created_at, updated_at)
    VALUES %s
""", workflow_rows)
print(f"Created {len(workflow_rows)} workflows")

# ─── ESCALATION POLICIES (4) ────────────────────────────────────
esc_rows = []
esc_data = [
    ("Critical Service Escalation", "api-server", ["critical", "high"],
     [{"level": 1, "notify": ["oncall-primary"], "wait_minutes": 5},
      {"level": 2, "notify": ["oncall-secondary", "team-lead"], "wait_minutes": 15},
      {"level": 3, "notify": ["engineering-manager", "vp-engineering"], "wait_minutes": 30}]),
    ("Database Escalation", "database", ["critical"],
     [{"level": 1, "notify": ["dba-oncall"], "wait_minutes": 5},
      {"level": 2, "notify": ["dba-lead", "infra-manager"], "wait_minutes": 10}]),
    ("Payment Gateway Escalation", "payment-gateway", ["critical", "high"],
     [{"level": 1, "notify": ["payments-oncall"], "wait_minutes": 3},
      {"level": 2, "notify": ["payments-lead", "cto"], "wait_minutes": 10}]),
    ("Default Escalation", None, ["critical"],
     [{"level": 1, "notify": ["oncall-primary"], "wait_minutes": 10},
      {"level": 2, "notify": ["engineering-manager"], "wait_minutes": 30}]),
]
for name, svc, sevs, levels in esc_data:
    esc_rows.append((uid(), user_id, name, svc, json.dumps(sevs), json.dumps(levels),
                     True, NOW - timedelta(days=15), NOW))

execute_values(cur, """
    INSERT INTO escalation_policies (id, user_id, name, service_name, severity_levels, levels,
        enabled, created_at, updated_at)
    VALUES %s
""", esc_rows)
print(f"Created {len(esc_rows)} escalation policies")

# ─── MAINTENANCE WINDOWS (5) ────────────────────────────────────
maint_rows = []
maint_data = [
    ("Database Upgrade to PostgreSQL 16", "Major version upgrade with zero-downtime migration",
     ["database"], ["backup", "upgrade", "verify", "failover"], "completed"),
    ("Redis Cluster Expansion", "Adding 2 new nodes to Redis cluster",
     ["redis-cache"], ["add_nodes", "rebalance", "verify"], "completed"),
    ("API Server Certificate Rotation", "Rotating TLS certificates for all API endpoints",
     ["api-server", "auth-service"], ["generate_certs", "deploy", "verify"], "completed"),
    ("Network Security Patch", "Applying critical security patch to all nodes",
     ["api-server", "database", "redis-cache", "auth-service"], ["patch", "restart", "verify"], "scheduled"),
    ("Storage Migration to GP3", "Migrating EBS volumes from GP2 to GP3",
     ["database"], ["snapshot", "migrate", "verify", "cleanup"], "scheduled"),
]
for i, (title, desc, services, actions_list, status) in enumerate(maint_data):
    if status == "completed":
        start = NOW - timedelta(days=random.randint(3, 20))
        end = start + timedelta(hours=random.randint(2, 6))
        actual_start = start + timedelta(minutes=random.randint(0, 15))
        actual_end = end - timedelta(minutes=random.randint(0, 30))
    else:
        start = NOW + timedelta(days=random.randint(1, 7))
        end = start + timedelta(hours=random.randint(2, 4))
        actual_start = None
        actual_end = None
    maint_rows.append((uid(), user_id, title, desc, start, end,
                       json.dumps(services), json.dumps(actions_list), status,
                       True, status == "completed",
                       json.dumps({"success": True, "notes": "Completed without issues"}) if status == "completed" else None,
                       actual_start, actual_end, NOW - timedelta(days=10), NOW))

execute_values(cur, """
    INSERT INTO maintenance_windows (id, user_id, title, description, start_time, end_time,
        affected_services, planned_actions, status, notification_sent, reminder_sent,
        completion_report, actual_start, actual_end, created_at, updated_at)
    VALUES %s
""", maint_rows)
print(f"Created {len(maint_rows)} maintenance windows")

# ─── CHAOS EXPERIMENTS (6) ───────────────────────────────────────
chaos_rows = []
chaos_data = [
    ("Pod Kill Test", "pod_kill", "api-server", {"target_pods": 1, "grace_period": 30}, 60, "completed",
     {"survived": True, "recovery_time_seconds": 12, "errors_during": 0, "availability": 99.98}),
    ("Network Latency Injection", "network_latency", "database", {"latency_ms": 200, "jitter_ms": 50}, 120, "completed",
     {"survived": True, "p99_increase_ms": 180, "error_rate_change": 0.1, "circuit_breaker_triggered": False}),
    ("CPU Stress Test", "cpu_stress", "api-server", {"cpu_percent": 90, "workers": 4}, 180, "completed",
     {"survived": True, "auto_scaled": True, "scale_time_seconds": 45, "max_response_time_ms": 2100}),
    ("Memory Pressure", "memory_stress", "auth-service", {"memory_percent": 85}, 120, "completed",
     {"survived": True, "oom_killed": False, "gc_pause_max_ms": 450, "requests_dropped": 3}),
    ("Dependency Failure", "dependency_kill", "payment-gateway", {"target": "stripe-api", "duration": 60}, 60, "completed",
     {"survived": True, "circuit_breaker_opened_at": 8, "fallback_success_rate": 95, "recovery_time": 5}),
    ("Zone Failure Simulation", "zone_failure", "api-server", {"zone": "us-east-1a"}, 300, "completed",
     {"survived": True, "failover_time_seconds": 18, "data_loss": False, "availability_during": 99.5}),
]
for name, etype, svc, config, dur, status, results in chaos_data:
    started = NOW - timedelta(days=random.randint(1, 14))
    chaos_rows.append((uid(), user_id, name, etype, svc, json.dumps(config), dur, status,
                       json.dumps(results),
                       json.dumps({"cpu_threshold": 95, "error_rate_threshold": 10, "auto_stop": True}),
                       started, started + timedelta(seconds=dur), started))

execute_values(cur, """
    INSERT INTO chaos_experiments (id, user_id, name, experiment_type, target_service, config,
        duration_seconds, status, results, safety_checks, started_at, completed_at, created_at)
    VALUES %s
""", chaos_rows)
print(f"Created {len(chaos_rows)} chaos experiments")

# ─── NOTIFICATION PREFERENCES ───────────────────────────────────
notif_rows = [
    (uid(), user_id, "slack", True, "medium", json.dumps([]), 23, 7, "daily", NOW, NOW),
    (uid(), user_id, "email", True, "high", json.dumps([]), None, None, "weekly", NOW, NOW),
]
execute_values(cur, """
    INSERT INTO notification_preferences (id, user_id, channel, enabled, severity_threshold,
        services, quiet_hours_start, quiet_hours_end, digest_frequency, created_at, updated_at)
    VALUES %s
""", notif_rows)
print("Created notification preferences")

# ─── FORECASTS (10) ─────────────────────────────────────────────
forecast_rows = []
for svc in SERVICES[:5]:
    for metric in ["cpu_percent", "memory_percent"]:
        data_points = []
        base = 45 if metric == "cpu_percent" else 60
        for h in range(0, 48):
            data_points.append({"hour": h, "value": round(base + h * 0.3 + random.gauss(0, 3), 1)})
        trend = random.choice(["increasing", "stable", "decreasing"])
        breach = trend == "increasing" and random.random() < 0.4
        forecast_rows.append((uid(), svc, metric, "time_series", 48, "prophet",
                             json.dumps(data_points), trend, breach,
                             round(random.uniform(12, 48), 1) if breach else None,
                             round(random.uniform(0.75, 0.95), 2), NOW))

execute_values(cur, """
    INSERT INTO forecasts (id, service_name, metric_name, forecast_type, horizon_hours, method,
        forecast_data, trend_direction, breach_predicted, hours_until_breach, confidence, created_at)
    VALUES %s
""", forecast_rows)
print(f"Created {len(forecast_rows)} forecasts")

# ─── CAPACITY PLANS (6) ─────────────────────────────────────────
cap_rows = []
cap_data = [
    ("api-server", "scaling", "Black Friday Prep", 65, 92, "Scale to 15 pods, increase memory to 4GB per pod", 10, 450),
    ("database", "storage", "Q2 Growth", 78, 95, "Expand storage to 500GB, upgrade to r6g.xlarge", 0, 380),
    ("redis-cache", "memory", "Cache Expansion", 72, 88, "Add 2 nodes to cluster, increase memory to 8GB", 2, 200),
    ("payment-gateway", "scaling", "Holiday Season", 55, 85, "Scale to 8 pods, add connection pooler", 5, 300),
    ("notification-service", "queue", "Marketing Campaign", 40, 78, "Increase queue capacity, add 3 consumers", 3, 150),
    ("auth-service", "scaling", "User Growth", 60, 82, "Scale to 6 pods, optimize token cache", 3, 180),
]
for svc, ptype, event, current, predicted, rec, instances, cost in cap_data:
    cap_rows.append((uid(), svc, ptype, event, current, predicted, rec, instances, cost,
                     json.dumps({"timeline": "2 weeks", "priority": "high"}),
                     random.choice(["proposed", "approved", "in_progress"]), NOW))

execute_values(cur, """
    INSERT INTO capacity_plans (id, service_name, plan_type, event_name, current_utilization,
        predicted_utilization, recommendation, additional_instances, estimated_cost, plan_data,
        status, created_at)
    VALUES %s
""", cap_rows)
print(f"Created {len(cap_rows)} capacity plans")

# ─── COST FORECASTS (4) ────────────────────────────────────────
cost_rows = []
for period, ftype, current, predicted in [
    ("monthly", "infrastructure", 12500, 14200),
    ("monthly", "compute", 8200, 9800),
    ("quarterly", "total", 38000, 43500),
    ("monthly", "storage", 2100, 2650),
]:
    cost_rows.append((uid(), period, ftype, current, predicted,
                      json.dumps({"compute": 8200, "storage": 2100, "network": 1200, "other": 1000}),
                      json.dumps([
                          {"action": "Right-size api-server pods", "savings": 320, "effort": "low"},
                          {"action": "Use spot instances for workers", "savings": 580, "effort": "medium"},
                          {"action": "Optimize log retention", "savings": 150, "effort": "low"},
                      ]),
                      round(random.uniform(0.85, 0.95), 2), NOW))

execute_values(cur, """
    INSERT INTO cost_forecasts (id, period, forecast_type, current_cost, predicted_cost,
        cost_breakdown, optimizations, accuracy, created_at)
    VALUES %s
""", cost_rows)
print(f"Created {len(cost_rows)} cost forecasts")

# ─── SLA CONFIGS (ensure they exist) ────────────────────────────
for svc, target in [("api-server", 99.95), ("database", 99.99), ("auth-service", 99.9),
                     ("payment-gateway", 99.95), ("redis-cache", 99.9), ("notification-service", 99.5)]:
    cur.execute("SELECT 1 FROM sla_configs WHERE user_id = %s AND service_name = %s", (user_id, svc))
    if not cur.fetchone():
        budget = round((100 - target) * 43200 / 100, 1)
        cur.execute("INSERT INTO sla_configs (id, user_id, service_name, target_uptime, max_mttr_minutes, error_budget_minutes) VALUES (%s,%s,%s,%s,%s,%s)",
                    (uid(), user_id, svc, target, 30, budget))
print("SLA configs verified")

# ─── MARKETPLACE (ensure they exist) ────────────────────────────
mp_items = [
    ("Kubernetes Scaler Agent", "Auto-scales K8s deployments based on real-time metrics and predicted load", "agent", "infrastructure", 2340, 4.7, ["kubernetes","auto-scaling","HPA"]),
    ("Slack Incident Bot", "Creates Slack channels for incidents, posts updates, manages war rooms", "plugin", "communication", 5120, 4.9, ["slack","incidents","notifications"]),
    ("Cost Anomaly Detector", "ML-based detection of unexpected cost spikes across cloud providers", "agent", "cost-optimization", 1890, 4.5, ["cost","anomaly","AWS","GCP"]),
    ("Database Health Monitor", "Deep PostgreSQL monitoring: slow queries, locks, vacuum stats", "agent", "database", 3450, 4.8, ["postgresql","monitoring","performance"]),
    ("CI/CD Pipeline Analyzer", "Analyzes build times, failure rates, and deployment frequency", "dashboard", "devops", 1560, 4.3, ["CI/CD","GitHub Actions","builds"]),
    ("Incident Postmortem Generator", "Auto-generates detailed postmortems from incident data", "report", "documentation", 4200, 4.6, ["postmortem","reports","blameless"]),
    ("Security Compliance Scanner", "Continuous compliance checking for SOC2, GDPR, ISO 27001", "agent", "security", 2780, 4.4, ["security","compliance","SOC2"]),
    ("Multi-Cloud Network Monitor", "Cross-cloud network latency, packet loss, and routing analysis", "agent", "networking", 980, 4.1, ["network","multi-cloud","latency"]),
    ("Canary Deployment Workflow", "Automated canary rollouts with traffic shifting and rollback", "workflow", "deployment", 3100, 4.7, ["canary","deployment","rollback"]),
    ("Log Pattern Analyzer", "ML-powered log clustering and anomaly detection", "agent", "observability", 1740, 4.2, ["logs","ML","clustering"]),
]
mp_count = 0
for name, desc, itype, cat, dl, rating, tags in mp_items:
    cur.execute("SELECT 1 FROM marketplace_items WHERE name = %s", (name,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO marketplace_items (id, name, description, item_type, category,
            author_name, version, downloads, rating, review_count, verified, tags)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (uid(), name, desc, itype, cat, "Community", "1.0.0",
             dl, rating, random.randint(10, 80), rating >= 4.5, json.dumps(tags)))
        mp_count += 1
print(f"Created {mp_count} marketplace items")

# ─── COMMIT ─────────────────────────────────────────────────────
conn.commit()
cur.close()
conn.close()
print("\n=== RICH DEMO DATA SEEDED SUCCESSFULLY ===")
print("Login: aidevops@demo.com / har@2410")
