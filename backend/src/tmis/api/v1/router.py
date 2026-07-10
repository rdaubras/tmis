from fastapi import APIRouter

from tmis.api.v1.case.routes import router as case_router
from tmis.api.v1.case_intelligence.routes import router as case_intelligence_router
from tmis.api.v1.health.routes import router as health_router
from tmis.legal_research.api.routes import router as legal_research_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(case_router)
api_router.include_router(case_intelligence_router)
api_router.include_router(legal_research_router)
