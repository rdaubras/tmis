from fastapi import APIRouter

from tmis.ai_team.api.routes import router as ai_team_router
from tmis.api.v1.case.routes import router as case_router
from tmis.api.v1.case_intelligence.routes import router as case_intelligence_router
from tmis.api.v1.health.routes import router as health_router
from tmis.cabinet_knowledge.api.routes import router as cabinet_knowledge_router
from tmis.cabinet_os.api.routes import router as cabinet_os_router
from tmis.collaboration.api.routes import router as collaboration_router
from tmis.legal_drafting.api.routes import router as legal_drafting_router
from tmis.legal_reasoning.api.routes import router as legal_reasoning_router
from tmis.legal_research.api.routes import router as legal_research_router
from tmis.platform_sdk.api.routes import router as platform_sdk_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(case_router)
api_router.include_router(case_intelligence_router)
api_router.include_router(legal_research_router)
api_router.include_router(legal_reasoning_router)
api_router.include_router(legal_drafting_router)
api_router.include_router(collaboration_router)
api_router.include_router(cabinet_os_router)
api_router.include_router(ai_team_router)
api_router.include_router(cabinet_knowledge_router)
api_router.include_router(platform_sdk_router)
