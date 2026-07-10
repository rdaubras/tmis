from fastapi import APIRouter, Depends, HTTPException

from tmis.cabinet_os.administration.engine import AdministrationEngine
from tmis.cabinet_os.administration.schemas import FirmRecord, FirmStatus
from tmis.cabinet_os.api.schemas import (
    ConnectorStatusResponse,
    FirmRecordResponse,
    MonitoringSnapshotResponse,
    RegisterConnectorRequest,
    RegisterFirmRequest,
    SetFirmStatusRequest,
    SetGlobalConfigRequest,
)
from tmis.cabinet_os.bootstrap import get_administration_engine

router = APIRouter(prefix="/cabinet-os/administration", tags=["cabinet-os-administration"])


def _to_firm_response(firm: FirmRecord) -> FirmRecordResponse:
    return FirmRecordResponse(id=firm.id, name=firm.name, status=firm.status.value)


@router.post("/firms", response_model=FirmRecordResponse)
def register_firm(
    payload: RegisterFirmRequest, engine: AdministrationEngine = Depends(get_administration_engine)
) -> FirmRecordResponse:
    return _to_firm_response(engine.register_firm(payload.name))


@router.get("/firms", response_model=list[FirmRecordResponse])
def list_firms(
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> list[FirmRecordResponse]:
    return [_to_firm_response(f) for f in engine.list_firms()]


@router.post("/firms/{firm_id}/status", response_model=FirmRecordResponse)
def set_firm_status(
    firm_id: str,
    payload: SetFirmStatusRequest,
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> FirmRecordResponse:
    try:
        status = FirmStatus(payload.status)
        firm = engine.set_firm_status(firm_id, status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_firm_response(firm)


@router.post("/connectors", response_model=ConnectorStatusResponse)
def register_connector(
    payload: RegisterConnectorRequest,
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> ConnectorStatusResponse:
    connector = engine.register_connector(payload.name, payload.connector_type)
    return ConnectorStatusResponse(
        name=connector.name, connector_type=connector.connector_type, enabled=connector.enabled
    )


@router.get("/connectors", response_model=list[ConnectorStatusResponse])
def list_connectors(
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> list[ConnectorStatusResponse]:
    return [
        ConnectorStatusResponse(name=c.name, connector_type=c.connector_type, enabled=c.enabled)
        for c in engine.list_connectors()
    ]


@router.post("/config")
def set_global_config(
    payload: SetGlobalConfigRequest,
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> dict[str, str]:
    entry = engine.set_global_config(payload.key, payload.value)
    return {"key": entry.key, "value": entry.value}


@router.get("/monitoring", response_model=MonitoringSnapshotResponse)
def monitoring_snapshot(
    engine: AdministrationEngine = Depends(get_administration_engine),
) -> MonitoringSnapshotResponse:
    snapshot = engine.monitoring_snapshot()
    return MonitoringSnapshotResponse(
        cpu_percent=snapshot.cpu_percent,
        memory_percent=snapshot.memory_percent,
        request_latency_ms_p50=snapshot.request_latency_ms_p50,
        request_latency_ms_p95=snapshot.request_latency_ms_p95,
        error_rate=snapshot.error_rate,
    )
