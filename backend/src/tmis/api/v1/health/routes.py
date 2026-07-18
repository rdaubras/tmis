from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Liveness alias, not a readiness check: always `{"status": "ok"}`
    once the process can respond at all, deliberately independent of
    every downstream dependency (see docs/49-guide-supervision.md —
    Health checks). Use `GET /platform/health/ready` to know whether
    the database/queue actually answer."""
    return {"status": "ok"}
