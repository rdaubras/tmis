from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tmis.api.v1.router import api_router
from tmis.core.config import get_settings
from tmis.core.logging import configure_logging
from tmis.core.observability import trace_id_middleware

settings = get_settings()
configure_logging(debug=settings.debug)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Legal Operating System — API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(trace_id_middleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "running"}
