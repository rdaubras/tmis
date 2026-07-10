from fastapi import APIRouter

from tmis.cabinet_os.api.administration_routes import router as administration_router
from tmis.cabinet_os.api.billing_routes import router as billing_router
from tmis.cabinet_os.api.calendar_routes import router as calendar_router
from tmis.cabinet_os.api.crm_routes import router as crm_router
from tmis.cabinet_os.api.operations_routes import router as operations_router
from tmis.cabinet_os.api.public_api_routes import router as public_api_router

router = APIRouter()
router.include_router(crm_router)
router.include_router(calendar_router)
router.include_router(billing_router)
router.include_router(operations_router)
router.include_router(administration_router)
router.include_router(public_api_router)
