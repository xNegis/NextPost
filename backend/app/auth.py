import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Account


def load_account(session: Session, account_id: str) -> Account | None:
    try:
        account_uuid = uuid.UUID(account_id)
    except (TypeError, ValueError):
        return None
    return session.get(Account, account_uuid)


def get_current_account(request: Request, session: Session = Depends(get_db_session)) -> Account:
    account_id = request.session.get("account_id")
    if not isinstance(account_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )
    account = load_account(session, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthenticated"},
        )
    return account
