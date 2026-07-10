from fastapi import APIRouter, Depends, HTTPException, Response

from tmis.cabinet_os.analytics.engine import AnalyticsEngine
from tmis.cabinet_os.api.schemas import (
    AdminDashboardResponse,
    CabinetDashboardResponse,
    CabinetDocumentResponse,
    CollaboratorDashboardResponse,
    FirmAnalyticsResponse,
    GenerateReportRequest,
    RegisterDocumentRequest,
    SetSettingRequest,
    SettingResponse,
)
from tmis.cabinet_os.bootstrap import (
    get_analytics_engine,
    get_cabinet_document_service,
    get_dashboard_engine,
    get_report_engine,
    get_settings_engine,
)
from tmis.cabinet_os.dashboard.engine import DashboardEngine
from tmis.cabinet_os.documents.schemas import CabinetDocument, DocumentCategory
from tmis.cabinet_os.documents.service import CabinetDocumentService
from tmis.cabinet_os.reports.engine import ReportEngine
from tmis.cabinet_os.reports.schemas import ReportFormat, ReportTable
from tmis.cabinet_os.settings.engine import SettingsEngine
from tmis.cabinet_os.settings.schemas import SettingsCategory

router = APIRouter(prefix="/cabinet-os", tags=["cabinet-os-operations"])


def _to_document_response(document: CabinetDocument) -> CabinetDocumentResponse:
    return CabinetDocumentResponse(
        id=document.id,
        firm_id=document.firm_id,
        client_id=document.client_id,
        filename=document.filename,
        category=document.category.value,
        case_id=document.case_id,
    )


@router.post("/documents", response_model=CabinetDocumentResponse)
def register_document(
    payload: RegisterDocumentRequest,
    service: CabinetDocumentService = Depends(get_cabinet_document_service),
) -> CabinetDocumentResponse:
    try:
        category = DocumentCategory(payload.category)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown document category: {payload.category!r}"
        ) from exc
    document = service.register(
        payload.firm_id,
        payload.client_id,
        payload.filename,
        payload.storage_ref,
        category=category,
        case_id=payload.case_id,
    )
    return _to_document_response(document)


@router.get("/documents", response_model=list[CabinetDocumentResponse])
def list_documents_for_client(
    client_id: str, service: CabinetDocumentService = Depends(get_cabinet_document_service)
) -> list[CabinetDocumentResponse]:
    return [_to_document_response(d) for d in service.list_for_client(client_id)]


@router.get("/dashboard/cabinet/{firm_id}", response_model=CabinetDashboardResponse)
def cabinet_dashboard(
    firm_id: str, engine: DashboardEngine = Depends(get_dashboard_engine)
) -> CabinetDashboardResponse:
    dashboard = engine.cabinet_dashboard(firm_id)
    return CabinetDashboardResponse(
        firm_id=dashboard.firm_id,
        revenue=dashboard.revenue,
        open_case_count=dashboard.open_case_count,
        hearing_count=dashboard.hearing_count,
        billable_minutes=dashboard.billable_minutes,
        ai_requests=dashboard.ai_requests,
    )


@router.get(
    "/dashboard/collaborator/{firm_id}/{collaborator_id}",
    response_model=CollaboratorDashboardResponse,
)
def collaborator_dashboard(
    firm_id: str, collaborator_id: str, engine: DashboardEngine = Depends(get_dashboard_engine)
) -> CollaboratorDashboardResponse:
    dashboard = engine.collaborator_dashboard(firm_id, collaborator_id)
    return CollaboratorDashboardResponse(
        collaborator_id=dashboard.collaborator_id,
        task_count=dashboard.task_count,
        open_task_count=dashboard.open_task_count,
        case_count=dashboard.case_count,
        upcoming_deadline_count=dashboard.upcoming_deadline_count,
        tracked_minutes=dashboard.tracked_minutes,
    )


@router.get("/dashboard/admin/{firm_id}", response_model=AdminDashboardResponse)
def admin_dashboard(
    firm_id: str, engine: DashboardEngine = Depends(get_dashboard_engine)
) -> AdminDashboardResponse:
    try:
        dashboard = engine.admin_dashboard(firm_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminDashboardResponse(
        firm_id=dashboard.firm_id,
        plan=dashboard.plan,
        active_users=dashboard.active_users,
        max_users=dashboard.max_users,
        storage_gb_used=dashboard.storage_gb_used,
        max_storage_gb=dashboard.max_storage_gb,
        ai_requests_used=dashboard.ai_requests_used,
        max_ai_requests_per_month=dashboard.max_ai_requests_per_month,
    )


@router.get("/analytics/{firm_id}", response_model=FirmAnalyticsResponse)
def firm_analytics(
    firm_id: str, engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> FirmAnalyticsResponse:
    analytics = engine.compute_firm_analytics(firm_id)
    return FirmAnalyticsResponse(
        firm_id=analytics.firm_id,
        client_count=analytics.client_count,
        active_client_count=analytics.active_client_count,
        document_count=analytics.document_count,
        billable_minutes=analytics.billable_minutes,
        non_billable_minutes=analytics.non_billable_minutes,
        ai_requests=analytics.ai_requests,
        average_minutes_per_case=analytics.average_minutes_per_case,
    )


@router.post("/reports/generate")
def generate_report(
    payload: GenerateReportRequest, engine: ReportEngine = Depends(get_report_engine)
) -> Response:
    try:
        report_format = ReportFormat(payload.report_format)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Unknown report format: {payload.report_format!r}"
        ) from exc
    table = ReportTable(title=payload.title, headers=payload.headers, rows=payload.rows)
    result = engine.generate(table, report_format)
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )


@router.get("/settings/{firm_id}/{category}/{key}", response_model=SettingResponse)
def get_setting(
    firm_id: str,
    category: str,
    key: str,
    engine: SettingsEngine = Depends(get_settings_engine),
) -> SettingResponse:
    try:
        parsed_category = SettingsCategory(category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category!r}") from exc
    value = engine.get(firm_id, parsed_category, key, default="")
    return SettingResponse(firm_id=firm_id, category=category, key=key, value=value or "")


@router.post("/settings/{firm_id}/{category}/{key}", response_model=SettingResponse)
def set_setting(
    firm_id: str,
    category: str,
    key: str,
    payload: SetSettingRequest,
    engine: SettingsEngine = Depends(get_settings_engine),
) -> SettingResponse:
    try:
        parsed_category = SettingsCategory(category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category!r}") from exc
    entry = engine.set(firm_id, parsed_category, key, payload.value)
    return SettingResponse(
        firm_id=entry.firm_id, category=entry.category.value, key=entry.key, value=entry.value
    )
