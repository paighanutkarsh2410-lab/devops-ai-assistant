from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.incidents import router as incidents_router
from routes.metrics import router as metrics_router
from routes.alerts import router as alerts_router
from routes.logs import router as logs_router
from routes.deployments import router as deployments_router
from websocket.handlers import router as ws_router
from monitoring.prometheus_exporter import PrometheusMiddleware, metrics_endpoint
from monitoring.metric_generator import start_metric_generator

app = FastAPI(title="DevOps AI Assistant API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(metrics_router)
app.include_router(alerts_router)
app.include_router(logs_router)
app.include_router(deployments_router)
app.include_router(ws_router)

# Prometheus metrics endpoint
app.add_route("/metrics", metrics_endpoint)


@app.on_event("startup")
async def startup():
    start_metric_generator()


@app.get("/")
def read_root():
    return {
        "message": "DevOps AI Assistant API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
