from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tmis.api.v1.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from tmis.application.identity.commands import (
    AuthResult,
    InvalidCredentialsError,
    LoginCommand,
    LoginUseCase,
    RefreshCommand,
    RefreshUseCase,
)
from tmis.core.database import get_db_session
from tmis.infrastructure.persistence.repositories import SqlAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

# One generic message for every login/refresh failure — never tells the
# caller whether the email exists, the password was wrong, the account
# is inactive, or the refresh token expired (no account-enumeration
# signal, see docs/07-strategie-securite.md).
_INVALID_CREDENTIALS_DETAIL = "Identifiants invalides."


def _token_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    use_case = LoginUseCase(SqlAlchemyUserRepository(session))
    try:
        result = use_case.execute(LoginCommand(email=payload.email, password=payload.password))
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=_INVALID_CREDENTIALS_DETAIL) from exc
    return _token_response(result)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    use_case = RefreshUseCase(SqlAlchemyUserRepository(session))
    try:
        result = use_case.execute(RefreshCommand(refresh_token=payload.refresh_token))
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=_INVALID_CREDENTIALS_DETAIL) from exc
    return _token_response(result)
