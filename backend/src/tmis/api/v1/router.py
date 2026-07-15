from fastapi import APIRouter

from tmis.ai_fabric.api.routes import router as ai_fabric_router
from tmis.ai_governance.api.routes import router as ai_governance_router
from tmis.ai_team.api.routes import router as ai_team_router
from tmis.api.v1.case.routes import router as case_router
from tmis.api.v1.case_intelligence.routes import router as case_intelligence_router
from tmis.api.v1.chat.routes import router as chat_router
from tmis.api.v1.document.routes import router as document_router
from tmis.api.v1.health.routes import router as health_router
from tmis.api.v1.watch.routes import router as watch_router
from tmis.business_platform.api.routes import router as business_platform_router
from tmis.cabinet_knowledge.api.routes import router as cabinet_knowledge_router
from tmis.cabinet_os.api.routes import router as cabinet_os_router
from tmis.collaboration.api.routes import router as collaboration_router
from tmis.identity_platform.api.routes import router as identity_platform_router
from tmis.integration_hub.api.routes import router as integration_hub_router
from tmis.legal_copilot_framework.api.routes import router as legal_copilot_framework_router
from tmis.legal_drafting.api.routes import router as legal_drafting_router
from tmis.legal_knowledge_graph.api.routes import router as legal_knowledge_graph_router
from tmis.legal_reasoning.api.routes import router as legal_reasoning_router
from tmis.legal_research.api.routes import router as legal_research_router
from tmis.platform_sdk.api.routes import router as platform_sdk_router
from tmis.strategic_intelligence.api.routes import router as strategic_intelligence_router
from tmis.workflow_automation.api.routes import router as workflow_automation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(case_router)
api_router.include_router(case_intelligence_router)
api_router.include_router(chat_router)
api_router.include_router(document_router)
api_router.include_router(watch_router)
api_router.include_router(legal_research_router)
api_router.include_router(legal_reasoning_router)
api_router.include_router(legal_drafting_router)
api_router.include_router(collaboration_router)
api_router.include_router(cabinet_os_router)
api_router.include_router(ai_team_router)
api_router.include_router(cabinet_knowledge_router)
api_router.include_router(platform_sdk_router)
api_router.include_router(ai_fabric_router)
api_router.include_router(ai_governance_router)
api_router.include_router(strategic_intelligence_router)
api_router.include_router(workflow_automation_router)
api_router.include_router(integration_hub_router)
api_router.include_router(identity_platform_router)
api_router.include_router(business_platform_router)
api_router.include_router(legal_copilot_framework_router)
api_router.include_router(legal_knowledge_graph_router)
