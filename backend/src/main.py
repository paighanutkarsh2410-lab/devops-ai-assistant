from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from routes.auth import router as auth_router
from routes.incidents import router as incidents_router
from routes.metrics import router as metrics_router
from routes.alerts import router as alerts_router
from routes.logs import router as logs_router
from routes.deployments import router as deployments_router
from routes.approvals import router as approvals_router
from routes.audit import router as audit_router
from routes.learning import router as learning_router
from routes.reports import router as reports_router
from routes.predictions import router as predictions_router
from routes.chat import router as chat_router
from routes.preferences import router as preferences_router
from routes.comments import router as comments_router
from routes.analytics import router as analytics_router
from routes.report_builder import router as report_builder_router
from routes.trends import router as trends_router
from routes.sla import router as sla_router
from routes.costs import router as costs_router
from routes.workflows import router as workflows_router
from routes.escalation import router as escalation_router
from routes.runbooks import router as runbooks_router
from routes.maintenance import router as maintenance_router
from routes.integrations import router as integrations_router
from routes.chaos import router as chaos_router
from routes.explanations import router as explanations_router
from routes.agent_intelligence import router as agent_intelligence_router
from routes.custom_agents import router as custom_agents_router
from routes.marketplace import router as marketplace_router
from routes.agent_status import router as agent_status_router
from routes.compliance import router as compliance_router
from routes.secrets import router as secrets_router
from routes.security import router as security_router
from routes.disaster_recovery import router as dr_router
from routes.chaos_experiments import router as chaos_eng_router
from routes.db_optimization import router as db_optimization_router
from routes.feedback import router as feedback_router
from websocket.handlers import router as ws_router
from monitoring.prometheus_exporter import PrometheusMiddleware, metrics_endpoint
from monitoring.metric_generator import start_metric_generator
from middleware.security import SecurityHeadersMiddleware
from middleware.rate_limiter import RateLimitMiddleware
from middleware.cache import CacheMiddleware
import os
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="DevOps AI Assistant API",
    version="1.0.0",
    description="Autonomous infrastructure monitoring and management system with AI agents",
)

# ── Middleware stack (order matters: outermost first) ────────────────────

# Gzip compression (>1KB responses)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# Response caching
app.add_middleware(CacheMiddleware)

# CORS
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://*.vercel.app,https://devops-ai-assistant.vercel.app").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# ── Routers ─────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(metrics_router)
app.include_router(alerts_router)
app.include_router(logs_router)
app.include_router(deployments_router)
app.include_router(approvals_router)
app.include_router(audit_router)
app.include_router(learning_router)
app.include_router(reports_router)
app.include_router(predictions_router)
app.include_router(chat_router)
app.include_router(preferences_router)
app.include_router(comments_router)
app.include_router(analytics_router)
app.include_router(report_builder_router)
app.include_router(trends_router)
app.include_router(sla_router)
app.include_router(costs_router)
app.include_router(workflows_router)
app.include_router(escalation_router)
app.include_router(runbooks_router)
app.include_router(maintenance_router)
app.include_router(integrations_router)
app.include_router(chaos_router)
app.include_router(explanations_router)
app.include_router(agent_intelligence_router)
app.include_router(custom_agents_router)
app.include_router(marketplace_router)
app.include_router(agent_status_router)
app.include_router(compliance_router)
app.include_router(secrets_router)
app.include_router(security_router)
app.include_router(dr_router)
app.include_router(chaos_eng_router)
app.include_router(db_optimization_router)
app.include_router(feedback_router)
app.include_router(ws_router)

# Prometheus metrics endpoint
app.add_route("/metrics", metrics_endpoint)


@app.on_event("startup")
async def startup():
    start_metric_generator()
    # Apply database indexes on startup
    try:
        from models import engine
        from models.optimizations import apply_indexes
        from models.database import Base
        Base.metadata.create_all(bind=engine)
        apply_indexes(engine)
        logging.getLogger(__name__).info("Database indexes applied")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not apply indexes: {e}")


@app.get("/")
def read_root():
    return {
        "message": "DevOps AI Assistant API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """Health check with dependency status."""
    import redis
    health = {"status": "healthy", "api": True}

    # Check database
    try:
        from models import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        health["database"] = True
    except Exception:
        health["database"] = False
        health["status"] = "degraded"

    # Check Redis
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        r.ping()
        health["redis"] = True
    except Exception:
        health["redis"] = False

    return health


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
