from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.accounts_service import (
    DuplicateAliasError,
    DuplicateEmailError,
    authenticate_account,
    register_account,
)
from app.auth import load_account
from app.db import get_db_session
from app.models import Account
from app.schemas import (
    AccountCreateRequest,
    AccountSummary,
    ProfileResponse,
    SessionResponse,
    SignInRequest,
)

router = APIRouter(tags=["accounts"])


def _load_account(session: Session, account_id: str) -> Account | None:
    return load_account(session, account_id)


def _session_account(request: Request, session: Session) -> Account | None:
    account_id = request.session.get("account_id")
    if not isinstance(account_id, str):
        return None
    return _load_account(session, account_id)


@router.post(
    "/accounts",
    response_model=AccountSummary,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "Duplicate alias or email"},
    },
)
def create_account(
    payload: AccountCreateRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> AccountSummary:
    try:
        account = register_account(session, payload.email, payload.alias, payload.password)
    except DuplicateAliasError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "alias_unavailable"},
        ) from exc
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "registration_unavailable"},
        ) from exc

    request.session["account_id"] = str(account.id)
    return AccountSummary(id=str(account.id), alias=account.alias)


@router.get(
    "/session",
    response_model=SessionResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}},
)
def read_session(
    request: Request,
    session: Session = Depends(get_db_session),
) -> SessionResponse:
    account = _session_account(request, session)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )

    return SessionResponse(
        authenticated=True,
        account=AccountSummary(id=str(account.id), alias=account.alias),
    )


@router.get(
    "/profile",
    response_model=ProfileResponse,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"}},
)
def read_profile(
    request: Request,
    session: Session = Depends(get_db_session),
) -> ProfileResponse:
    account = _session_account(request, session)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )

    return ProfileResponse(email=account.email, nickname=account.alias)


@router.post(
    "/session",
    response_model=AccountSummary,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
    },
)
def create_session(
    payload: SignInRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> AccountSummary:
    # A sign-in attempt must never inherit a previously authenticated account.
    request.session.pop("account_id", None)
    account = authenticate_account(session, payload.email, payload.password)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials"},
        )

    request.session["account_id"] = str(account.id)
    return AccountSummary(id=str(account.id), alias=account.alias)


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
