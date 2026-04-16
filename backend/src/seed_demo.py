"""Seed the database with realistic demo data using raw SQL (no ORM imports needed)."""
import os
import uuid
import random
from datetime import datetime, timedelta, timezone
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://devops_user:devops_password_123@localhost:5432/devops_ai")

NOW = datetime.now(timezone.utc)
SERVICES = ['api-server', 'database', 'redis-cache', 'auth-service', 'payment-gateway', 'notification-service']


def uid():
    return str(uuid.uuid4())


def seed():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # ── 1. Get or create demo user ──────────────────────────
    cur.execute("SELECT id FROM users WHERE email = 'aidevops@demo.com'")
    row = cur.fetchone()
    if row:
        user_id = str(row[0])
        print(f"Using existing user: aidevops@demo.com (id={user_id})")
    else:
        user_id = uid()
        # bcrypt hash of "har@2410"
        hashed = "$2b$12$0DhFt17acDlUnDa194H3duGh2nYZW1urt4VRUnmlG0gf8szUnXype"
        cur.execute("""
            INSERT INTO users (id, email, hashed_password, full_name, company, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, 'aidevops@demo.com', hashed, 'Utkarsh', 'DevOps AI', True, NOW))
        print(f"Created demo user: aidevops@demo.com / har@2410")

    # ── 2. Clear existing seed data ─────────────────────────
    print("Clearing old seed data...")
    cur.execute("DELETE FROM action_logs WHERE executed_by = 'remediation-agent'")
    cur.execute("DELETE FROM alerts WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM metrics WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM incidents WHERE user_id = %s", (user_id,))
    cur.execute("DELETE FROM deployments WHERE user_id = %s", (user_id,))

    # ── 3. Incidents (20 realistic ones) ────────────────────
    incident_templates = [
        ("API Response Time Degradation", "api-server", "high", "resolved",
         "P95 response time exceeded 2s threshold for 15 minutes",
         "Database connection pool exhaustion due to long-running queries",
         "Increased pool size from 10 to 25, optimized slow query on users table"),
        ("Memory Leak in Auth Service", "auth-service", "critical", "resolved",
         "Memory usage grew from 512MB to 3.8GB over 6 hours",
         "JWT token cache not evicting expired tokens, growing unbounded",
         "Added TTL-based eviction policy, deployed hotfix v2.4.1"),
        ("Redis Cache Miss Rate Spike", "redis-cache", "medium", "resolved",
         "Cache miss rate jumped from 5% to 45%",
         "Key expiry misconfiguration after deployment v3.1.0",
         "Rolled back cache TTL config, added monitoring for miss rate"),
        ("Database CPU at 95%", "database", "critical", "resolved",
         "PostgreSQL CPU sustained above 90% for 20 minutes",
         "Unindexed query on payments table scanning 2M rows",
         "Added composite index on (user_id, created_at), CPU dropped to 30%"),
        ("Payment Gateway Timeout", "payment-gateway", "critical", "resolved",
         "Payment success rate dropped to 62% from 99.8%",
         "Upstream provider rate limiting due to retry storm",
         "Implemented exponential backoff, added circuit breaker"),
        ("Notification Delivery Delay", "notification-service", "low", "resolved",
         "Email delivery delayed by 15-30 minutes",
         "Queue backlog from batch marketing notification job",
         "Separated marketing queue from transactional, priority routing added"),
        ("SSL Certificate Near Expiry", "api-server", "medium", "resolved",
         "Certificate expiring in 48 hours, auto-renewal failing",
         "Auto-renewal cron job failed due to DNS timeout",
         "Fixed DNS resolver config, renewed certificate manually"),
        ("Disk Usage Critical on DB Server", "database", "high", "resolved",
         "Disk usage at 94%, database at risk of read-only mode",
         "WAL logs not being archived, growing at 2GB/hour",
         "Configured WAL archiving, cleaned old logs, added 100GB volume"),
        ("Auth Service 503 Errors", "auth-service", "high", "resolved",
         "12% of login requests returning 503 Service Unavailable",
         "Health check endpoint failing due to dependency on unreachable LDAP",
         "Made LDAP check non-blocking, added fallback auth path"),
        ("API Rate Limiting Misconfigured", "api-server", "medium", "resolved",
         "Internal API calls being rate limited, affecting dashboard data",
         "Rate limit set to 10 req/min instead of 1000 for internal service account",
         "Updated rate limit config for service accounts, deployed immediately"),
        ("Redis Cluster Failover", "redis-cache", "high", "resolved",
         "30-second cache unavailability during automatic failover",
         "Primary node OOM killed, sentinel triggered automatic failover",
         "Increased memory limit, added eviction policy, promoted replica"),
        ("CPU Spike on API Server", "api-server", "medium", "resolved",
         "CPU at 88% on 3 of 5 API pods, response time degraded",
         "Regex-based input validation causing catastrophic backtracking",
         "Replaced regex with optimized parser, added input length limit"),
        ("Database Connection Timeout", "database", "high", "resolved",
         "New connections failing with 'too many clients' error",
         "Max connections (100) reached due to leaked connections in worker pool",
         "Fixed connection leak in background job processor, set idle timeout"),
        ("Payment Webhook Failures", "payment-gateway", "medium", "resolved",
         "43 failed webhook deliveries in last hour",
         "Webhook endpoint returning 500 due to schema mismatch after provider update",
         "Updated webhook handler to accept new payload format, added versioning"),
        ("High Error Rate on /api/search", "api-server", "high", "resolved",
         "Search endpoint returning 500 for 8% of requests",
         "Elasticsearch cluster yellow status, 2 shards unassigned",
         "Rebalanced shards, increased replica count, fixed mapping conflict"),
        # 5 open/investigating incidents
        ("Memory Pressure on Cache Nodes", "redis-cache", "low", "investigating",
         "Memory usage at 78%, approaching eviction threshold",
         None, None),
        ("Notification Email Bounces", "notification-service", "medium", "open",
         "15% bounce rate on transactional emails",
         None, None),
        ("Auth Token Validation Slow", "auth-service", "medium", "investigating",
         "Token validation adding 200ms to every authenticated request",
         None, None),
        ("Cascading Failure: API to DB to Cache", "api-server", "critical", "open",
         "Multi-service degradation affecting 60% of requests for 8 minutes",
         None, None),
        ("Deployment Rollback: v3.2.0", "api-server", "high", "investigating",
         "Error rate jumped to 25% within 2 minutes of deployment",
         None, None),
    ]

    incident_ids = []
    for i, (title, service, severity, status, desc, root_cause, solution) in enumerate(incident_templates):
        inc_id = uid()
        incident_ids.append(inc_id)
        hours_ago = random.randint(2, 720)
        detected = NOW - timedelta(hours=hours_ago)
        is_resolved = status == "resolved"
        is_auto = is_resolved and random.random() < 0.5
        resolution_secs = random.randint(60, 1800) if is_resolved else None
        resolved_at = detected + timedelta(seconds=resolution_secs) if is_resolved else None

        cur.execute("""
            INSERT INTO incidents (id, user_id, title, description, severity, status, service_name,
                root_cause, solution, detected_at, resolved_at, auto_resolved, resolution_time_seconds, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (inc_id, user_id, title, desc, severity, status, service,
              root_cause, solution, detected, resolved_at, is_auto, resolution_secs, detected))

    print(f"Created {len(incident_templates)} incidents")

    # ── 4. Metrics (last 7 days, every 2 hours) ─────────────
    metric_count = 0
    for service in SERVICES[:4]:
        for metric_name in ['cpu_percent', 'memory_percent', 'response_time_ms']:
            base = {'cpu_percent': 35, 'memory_percent': 55, 'response_time_ms': 120}[metric_name]
            unit = {'cpu_percent': '%', 'memory_percent': '%', 'response_time_ms': 'ms'}[metric_name]
            for hours in range(0, 168, 2):
                ts = NOW - timedelta(hours=hours)
                noise = random.gauss(0, base * 0.15)
                hour_factor = 1 + 0.3 * abs(ts.hour - 14) / 14
                val = max(1, base * hour_factor + noise)
                cur.execute("""
                    INSERT INTO metrics (id, user_id, service_name, metric_name, value, unit, timestamp)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (uid(), user_id, service, metric_name, round(val, 1), unit, ts))
                metric_count += 1
    print(f"Created {metric_count} metric data points")

    # ── 5. Alerts ───────────────────────────────────────────
    alert_data = [
        ("CPU usage above 80%", "api-server CPU at 87% for 5 minutes", "warning"),
        ("Memory critical: 92%", "auth-service memory approaching OOM limit", "critical"),
        ("Response time degraded", "P95 response time at 1.8s (threshold: 1s)", "warning"),
        ("Disk usage warning", "database disk at 85% capacity", "warning"),
        ("Error rate spike", "api-server error rate at 5.2% (threshold: 2%)", "critical"),
        ("Connection pool exhausted", "database connections at 98/100", "critical"),
        ("Cache hit rate low", "redis cache hit rate dropped to 60%", "info"),
        ("SSL certificate expiry", "api-server cert expires in 7 days", "info"),
    ]
    for j, (title, msg, sev) in enumerate(alert_data):
        hours_ago = random.randint(1, 72)
        triggered = NOW - timedelta(hours=hours_ago)
        ack = j < 5
        res = j < 3
        inc_id = incident_ids[j % len(incident_ids)] if j < 5 else None
        cur.execute("""
            INSERT INTO alerts (id, user_id, incident_id, title, message, severity,
                acknowledged, resolved, triggered_at, acknowledged_at, resolved_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid(), user_id, inc_id, title, msg, sev, ack, res, triggered,
              triggered + timedelta(hours=1) if ack else None,
              triggered + timedelta(hours=2) if res else None))
    print(f"Created {len(alert_data)} alerts")

    # ── 6. Action Logs ──────────────────────────────────────
    actions = [
        ("restart_service", "api-server", "success", 12.5),
        ("scale_up", "api-server", "success", 45.0),
        ("clear_cache", "redis-cache", "success", 3.2),
        ("rollback_deployment", "api-server", "success", 28.0),
        ("increase_resources", "database", "success", 60.0),
        ("restart_service", "auth-service", "success", 15.0),
        ("kill_process", "api-server", "success", 2.1),
        ("rate_limit_adjust", "api-server", "success", 1.5),
        ("restart_service", "payment-gateway", "failure", 30.0),
        ("scale_up", "notification-service", "success", 55.0),
        ("clear_cache", "redis-cache", "success", 2.8),
        ("rollback_deployment", "auth-service", "rollback", 35.0),
    ]
    for name, svc, status, dur in actions:
        inc_id = incident_ids[random.randint(0, len(incident_ids) - 1)]
        cur.execute("""
            INSERT INTO action_logs (id, incident_id, action_name, action_type, executed_by,
                executed_at, duration_seconds, status, impact_score, rollback_performed,
                approval_required, approved_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid(), inc_id, name, "remediation", "remediation-agent",
              NOW - timedelta(hours=random.randint(1, 200)), dur, status,
              round(random.uniform(0.3, 0.95), 2), status == "rollback",
              name in ["rollback_deployment", "increase_resources"],
              "admin@devops-ai.system" if name == "rollback_deployment" else None))
    print(f"Created {len(actions)} action logs")

    # ── 7. SLA Configs ──────────────────────────────────────
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='sla_configs')")
    if cur.fetchone()[0]:
        sla_count = 0
        for svc, target in [("api-server", 99.95), ("database", 99.99), ("auth-service", 99.9),
                             ("payment-gateway", 99.95), ("redis-cache", 99.9)]:
            cur.execute("SELECT 1 FROM sla_configs WHERE user_id = %s AND service_name = %s", (user_id, svc))
            if not cur.fetchone():
                budget = round((100 - target) * 43200 / 100, 1)
                cur.execute("""
                    INSERT INTO sla_configs (id, user_id, service_name, target_uptime,
                        max_mttr_minutes, error_budget_minutes)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (uid(), user_id, svc, target, 30, budget))
                sla_count += 1
        print(f"Created {sla_count} SLA configs")
    else:
        # Create the table
        cur.execute("""
            CREATE TABLE sla_configs (
                id VARCHAR PRIMARY KEY, user_id VARCHAR NOT NULL,
                service_name VARCHAR NOT NULL, target_uptime FLOAT DEFAULT 99.9,
                max_mttr_minutes INTEGER DEFAULT 30, max_incidents_per_month INTEGER,
                error_budget_minutes FLOAT DEFAULT 43.2, created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        for svc, target in [("api-server", 99.95), ("database", 99.99), ("auth-service", 99.9),
                             ("payment-gateway", 99.95), ("redis-cache", 99.9)]:
            budget = round((100 - target) * 43200 / 100, 1)
            cur.execute("""
                INSERT INTO sla_configs (id, user_id, service_name, target_uptime, max_mttr_minutes, error_budget_minutes)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (uid(), user_id, svc, target, 30, budget))
        print("Created sla_configs table + 5 SLA configs")

    # ── 8. Marketplace Items ────────────────────────────────
    cur.execute("SELECT EXISTS(SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='marketplace_items')")
    if cur.fetchone()[0]:
        mp_items = [
            ("Kubernetes Scaler Agent", "Auto-scales K8s deployments based on real-time metrics and predicted load", "agent", "infrastructure", 2340, 4.7, "kubernetes,auto-scaling,HPA"),
            ("Slack Incident Bot", "Creates Slack channels for incidents, posts updates, manages war rooms", "plugin", "communication", 5120, 4.9, "slack,incidents,notifications"),
            ("Cost Anomaly Detector", "ML-based detection of unexpected cost spikes across cloud providers", "agent", "cost-optimization", 1890, 4.5, "cost,anomaly,AWS,GCP"),
            ("Database Health Monitor", "Deep PostgreSQL monitoring: slow queries, locks, vacuum stats, replication lag", "agent", "database", 3450, 4.8, "postgresql,monitoring,performance"),
            ("CI/CD Pipeline Analyzer", "Analyzes build times, failure rates, and deployment frequency metrics", "dashboard", "devops", 1560, 4.3, "CI/CD,GitHub Actions,builds"),
            ("Incident Postmortem Generator", "Auto-generates detailed postmortems from incident timeline and resolution data", "report", "documentation", 4200, 4.6, "postmortem,reports,blameless"),
            ("Security Compliance Scanner", "Continuous compliance checking for SOC2, GDPR, and ISO 27001", "agent", "security", 2780, 4.4, "security,compliance,SOC2"),
            ("Multi-Cloud Network Monitor", "Cross-cloud network latency, packet loss, and routing analysis", "agent", "networking", 980, 4.1, "network,multi-cloud,latency"),
            ("Canary Deployment Workflow", "Automated canary rollouts with traffic shifting and automatic rollback", "workflow", "deployment", 3100, 4.7, "canary,deployment,rollback"),
            ("Log Pattern Analyzer", "ML-powered log clustering and anomaly detection across all services", "agent", "observability", 1740, 4.2, "logs,ML,clustering"),
        ]
        mp_count = 0
        for name, desc, itype, cat, dl, rating, tags in mp_items:
            cur.execute("SELECT 1 FROM marketplace_items WHERE name = %s", (name,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO marketplace_items (id, name, description, item_type, category,
                        author_name, version, downloads, rating, review_count, verified, tags)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (uid(), name, desc, itype, cat, "Community", "1.0.0",
                      dl, rating, random.randint(10, 80), rating >= 4.5,
                      '[' + ','.join(f'"{t}"' for t in tags.split(',')) + ']'))
                mp_count += 1
        print(f"Created {mp_count} marketplace items")
    else:
        print("Skipped marketplace_items (table not found)")

    # ── 9. Deployments ──────────────────────────────────────
    deploy_data = [
        ("api-server", "v3.2.1", "abc1234"), ("api-server", "v3.2.0", "def5678"),
        ("api-server", "v3.1.2", "ghi9012"), ("auth-service", "v2.4.1", "jkl3456"),
        ("auth-service", "v2.4.0", "mno7890"), ("database", "v1.8.0", "pqr1234"),
        ("payment-gateway", "v2.1.3", "stu5678"), ("redis-cache", "v1.2.0", "vwx9012"),
        ("notification-service", "v1.5.0", "yza3456"), ("api-server", "v3.1.1", "bcd7890"),
    ]
    for i, (svc, ver, commit) in enumerate(deploy_data):
        cur.execute("""
            INSERT INTO deployments (id, user_id, service_name, version, commit_hash,
                deployed_by, deployed_at, description)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid(), user_id, svc, ver, commit, "github-actions",
              NOW - timedelta(days=i * 2 + 1), f"Production deploy {ver}"))
    print(f"Created {len(deploy_data)} deployments")

    # ── Commit ──────────────────────────────────────────────
    conn.commit()
    cur.close()
    conn.close()
    print("\nDemo data seeded successfully!")
    print("Login: aidevops@demo.com / har@2410")


if __name__ == "__main__":
    seed()
