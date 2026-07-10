from fastapi import APIRouter, Depends, HTTPException

from tmis.cabinet_os.api.schemas import (
    ApiKeyResponse,
    IssueApiKeyRequest,
    IssueOAuthTokenRequest,
    OAuthClientResponse,
    OAuthTokenResponse,
    RegisterOAuthClientRequest,
)
from tmis.cabinet_os.bootstrap import get_public_api_engine
from tmis.cabinet_os.public_api.engine import PublicApiEngine
from tmis.cabinet_os.public_api.schemas import ApiScope

router = APIRouter(prefix="/public-api/v1", tags=["cabinet-os-public-api"])


def _parse_scopes(raw_scopes: list[str]) -> frozenset[ApiScope]:
    try:
        return frozenset(ApiScope(s) for s in raw_scopes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown scope in {raw_scopes!r}") from exc


@router.post("/keys", response_model=ApiKeyResponse)
def issue_api_key(
    payload: IssueApiKeyRequest, engine: PublicApiEngine = Depends(get_public_api_engine)
) -> ApiKeyResponse:
    scopes = _parse_scopes(payload.scopes)
    key, raw_key = engine.issue_api_key(payload.firm_id, payload.name, scopes)
    return ApiKeyResponse(
        id=key.id,
        firm_id=key.firm_id,
        name=key.name,
        prefix=key.prefix,
        scopes=[s.value for s in key.scopes],
        raw_key=raw_key,
    )


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyResponse)
def revoke_api_key(
    key_id: str, engine: PublicApiEngine = Depends(get_public_api_engine)
) -> ApiKeyResponse:
    try:
        key = engine.revoke_api_key(key_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ApiKeyResponse(
        id=key.id,
        firm_id=key.firm_id,
        name=key.name,
        prefix=key.prefix,
        scopes=[s.value for s in key.scopes],
    )


@router.get("/keys", response_model=list[ApiKeyResponse])
def list_api_keys(
    firm_id: str, engine: PublicApiEngine = Depends(get_public_api_engine)
) -> list[ApiKeyResponse]:
    return [
        ApiKeyResponse(
            id=k.id, firm_id=k.firm_id, name=k.name, prefix=k.prefix,
            scopes=[s.value for s in k.scopes],
        )
        for k in engine.list_api_keys(firm_id)
    ]


@router.post("/oauth/clients", response_model=OAuthClientResponse)
def register_oauth_client(
    payload: RegisterOAuthClientRequest, engine: PublicApiEngine = Depends(get_public_api_engine)
) -> OAuthClientResponse:
    scopes = _parse_scopes(payload.scopes)
    client, raw_secret = engine.register_oauth_client(
        payload.firm_id, payload.redirect_uris, scopes
    )
    return OAuthClientResponse(
        client_id=client.client_id,
        client_secret=raw_secret,
        scopes=[s.value for s in client.scopes],
    )


@router.post("/oauth/token", response_model=OAuthTokenResponse)
def issue_oauth_token(
    payload: IssueOAuthTokenRequest, engine: PublicApiEngine = Depends(get_public_api_engine)
) -> OAuthTokenResponse:
    try:
        token = engine.issue_oauth_token(payload.client_id, payload.client_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return OAuthTokenResponse(
        token=token.token, expires_at=token.expires_at, scopes=[s.value for s in token.scopes]
    )
