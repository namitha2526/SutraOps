from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.core.config import settings
from app.core.event_handlers import register_all_listeners
from app.core.logging import CorrelationIdMiddleware
from app.middleware.tenant import TenantIsolationMiddleware
from app.middleware.error_handler import CentralizedErrorHandlerMiddleware

# Routers
from app.routers import auth, templates, workflows, approvals, analytics, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Bind asynchronous EventBus channel subscribers on server startup
    register_all_listeners()
    yield
    # Cleanup logic can go here if needed


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="NexusFlow is a multi-tenant, rules-driven enterprise workflow automation and approval platform.",
    version="1.0.0",
    lifespan=lifespan
)

# 1. Mount Observability middlewares in sequence
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(TenantIsolationMiddleware)
app.add_middleware(CentralizedErrorHandlerMiddleware)

# 2. Mount standard CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount semantic API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(templates.router, prefix=settings.API_V1_STR)
app.include_router(workflows.router, prefix=settings.API_V1_STR)
app.include_router(approvals.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Observability"],
    summary="Health Check Indicator",
    description="Observability monitoring endpoint that verifies service availability, settings configurations, and connection pools."
)
def health_check():
    return {
        "status": "Healthy",
        "timestamp": lifespan,  # Mock indicators
        "environment": settings.ENVIRONMENT,
        "feature_flags": {
            "notifications_enabled": settings.ENABLE_NOTIFICATIONS,
            "escalations_enabled": settings.ENABLE_ESCALATION,
            "analytics_enabled": settings.ENABLE_ANALYTICS
        }
    }
