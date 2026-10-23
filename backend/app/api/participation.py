"""Authenticated participant-history read endpoint (RF-21).

This router exposes a single read-only ``GET /api/my-participation`` projection for the fifth
primary destination. The participant account is derived exclusively from the signed session; no
account, voter, owner, audience, state or capability selector is accepted. The service returns a
photo-free, keyset-paginated page that the router maps onto the strict response allowlist.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.auth import get_current_account
from app.db import get_db_session
from app.models import Account
from app.participation_service import (
    decode_history_cursor,
    list_participation_history,
)
from app.schemas import ParticipationItemResponse, ParticipationListResponse

router = APIRouter(tags=["participation"])


def _set_private_read_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"


def _event_at_iso(value: datetime) -> str:
    return value.isoformat() + "Z"


@router.get("/my-participation", response_model=ParticipationListResponse)
def my_participation(
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    response: Response = Response(),
) -> ParticipationListResponse:
    _set_private_read_headers(response)

    cursor_key = None
    if cursor is not None:
        decoded = decode_history_cursor(cursor)
        if decoded is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation_error",
                    "field_errors": {"cursor": "Enter a valid page cursor."},
                },
            )
        cursor_key = decoded

    page = list_participation_history(db, account.id, limit, cursor_key)

    items = [
        ParticipationItemResponse(
            consultation_id=item.consultation_id,
            status=item.status,
            event_kind=item.event_kind,
            event_at=_event_at_iso(item.event_at),
            can_view=item.can_view,
        )
        for item in page.items
    ]
    return ParticipationListResponse(items=items, next_cursor=page.next_cursor)
