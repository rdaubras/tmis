from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tmis.api.v1.router import api_router
from tmis.cloud_operations.api.routes import router as cloud_operations_router
from tmis.core.config import get_settings
from tmis.core.logging import configure_logging
from tmis.core.observability import trace_id_middleware
from tmis.platform.api.routes import router as platform_router
from tmis.platform.observability.middleware import correlation_middleware, metrics_middleware
from tmis.platform.security.csrf import csrf_middleware
from tmis.platform.security.headers import (
    CORS_ALLOWED_HEADERS,
    CORS_ALLOWED_METHODS,
    SecurityHeadersMiddleware,
    validate_cors_origins,
)

settings = get_settings()
configure_logging(debug=settings.debug)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Legal Operating System — API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=validate_cors_origins(settings.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=CORS_ALLOWED_METHODS,
    allow_headers=CORS_ALLOWED_HEADERS,
)

# Middleware added last runs first on the request (outermost); the order
# below is chosen so `trace_id_middleware` (sets `request.state.trace_id`)
# always runs before `correlation_middleware` (reads it), while security
# headers wrap the final response last.
app.middleware("http")(correlation_middleware)
app.middleware("http")(trace_id_middleware)
app.middleware("http")(csrf_middleware)
app.middleware("http")(metrics_middleware)
app.middleware("http")(SecurityHeadersMiddleware())

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(platform_router)
app.include_router(cloud_operations_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running"}
