"""Private account-linked participation-history projection (RF-21).

This module is the read boundary for the fifth primary destination. It builds one photo-free row
per consultation the authenticated account participated in by combining three mutually exclusive
sources in a single database-bounded union:

1. a real immutable ``Vote`` whose consultation is still ``open`` -> ``open``/``voted``;
2. a retained ``ConsultationOutcome`` -> ``matched``/``not_matched``/``no_choice``/``finalized``;
3. an exceptional surviving terminal ``Vote`` with no outcome -> ``unavailable``/``voted``.

Outcome precedence is enforced in both vote branches. Even if inconsistent stored state combines
an outcome with a residual vote or marks that consultation open again, each consultation yields at
most one row without an application-side dedupe.

The projection is photo-free by construction and scoped to the signed-session account inside SQL.
It never selects raw option IDs, images, question/context, author data, aggregate counts, a
Private-link capability or any administrative state; the frontend and API then apply an exact
response allowlist on top.

Pagination is deterministic descending keyset over ``(event_at, consultation_id)`` with an initial
server snapshot timestamp carried in every cursor. The snapshot upper-bounds events so a
consultation that finalizes during an older page simply disappears from that page rather than
duplicating or fabricating consistency; a fresh first-page load is authoritative.
"""

from __future__ import annotations

import base64
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import Boolean, Select, String, and_, cast, exists, literal, or_, select, union_all
from sqlalchemy.orm import Session

from app.audience import PUBLIC
from app.models import (
    Consultation,
    ConsultationFinalization,
    ConsultationOutcome,
    ConsultationState,
    Vote,
)
from app.photo_service import _as_naive_utc, utcnow

logger = logging.getLogger(__name__)

ParticipationStatus = Literal["open", "matched", "not_matched", "no_choice", "unavailable"]
ParticipationEventKind = Literal["voted", "finalized"]

_HISTORY_CURSOR_VERSION = "history-v1"
_HISTORY_CURSOR_MAX_LENGTH = 512


@dataclass(frozen=True)
class ParticipationItem:
    consultation_id: str
    status: ParticipationStatus
    event_kind: ParticipationEventKind
    event_at: datetime
    can_view: bool


@dataclass(frozen=True)
class ParticipationPage:
    items: list[ParticipationItem]
    next_cursor: str | None


def encode_history_cursor(
    snapshot: datetime, event_at: datetime, consultation_id: uuid.UUID
) -> str:
    """Encode a bounded, versioned keyset + snapshot cursor for this projection."""
    payload = json.dumps(
        [
            _HISTORY_CURSOR_VERSION,
            _as_naive_utc(snapshot).isoformat(),
            _as_naive_utc(event_at).isoformat(),
            str(consultation_id),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_history_cursor(raw: str) -> tuple[datetime, datetime, uuid.UUID] | None:
    """Decode and strictly validate a history cursor, or return ``None``.

    The cursor carries ``(snapshot, event_at, consultation_id)`` and is pagination state only. Any
    other version, shape, type, timezone-aware timestamp or malformed UUID is rejected.
    """
    if not isinstance(raw, str) or raw == "" or len(raw) > _HISTORY_CURSOR_MAX_LENGTH:
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        parsed = json.loads(decoded)
    except Exception:
        return None
    if not isinstance(parsed, list) or len(parsed) != 4:
        return None
    version, snapshot_text, event_text, consultation_id = parsed
    if version != _HISTORY_CURSOR_VERSION:
        return None
    if not all(isinstance(value, str) for value in (snapshot_text, event_text, consultation_id)):
        return None
    try:
        snapshot = datetime.fromisoformat(snapshot_text)
        event_at = datetime.fromisoformat(event_text)
    except ValueError:
        return None
    if snapshot.tzinfo is not None or event_at.tzinfo is not None:
        return None
    if event_at > snapshot:
        return None
    try:
        cid = uuid.UUID(consultation_id)
    except (TypeError, ValueError):
        return None
    return snapshot, event_at, cid


def _open_vote_select(account_id: uuid.UUID) -> Select[Any]:
    has_outcome = exists(
        select(ConsultationOutcome.id).where(
            ConsultationOutcome.consultation_id == Vote.consultation_id,
            ConsultationOutcome.voter_id == account_id,
        )
    )
    return (
        select(
            Vote.consultation_id.label("consultation_id"),
            Vote.created_at.label("event_at"),
            literal("open", String).label("status"),
            literal("voted", String).label("event_kind"),
            (Consultation.audience == PUBLIC).label("can_view"),
        )
        .join(Consultation, Consultation.id == Vote.consultation_id)
        .where(
            Vote.voter_id == account_id,
            Consultation.state == ConsultationState.open,
            ~has_outcome,
        )
    )


def _outcome_select(account_id: uuid.UUID) -> Select[Any]:
    return (
        select(
            ConsultationOutcome.consultation_id.label("consultation_id"),
            ConsultationFinalization.finalized_at.label("event_at"),
            cast(ConsultationOutcome.outcome, String).label("status"),
            literal("finalized", String).label("event_kind"),
            literal(False, Boolean).label("can_view"),
        )
        .join(
            ConsultationFinalization,
            ConsultationFinalization.consultation_id == ConsultationOutcome.consultation_id,
        )
        .where(ConsultationOutcome.voter_id == account_id)
    )


def _terminal_vote_select(account_id: uuid.UUID) -> Select[Any]:
    has_outcome = exists(
        select(ConsultationOutcome.id).where(
            ConsultationOutcome.consultation_id == Vote.consultation_id,
            ConsultationOutcome.voter_id == account_id,
        )
    )
    return (
        select(
            Vote.consultation_id.label("consultation_id"),
            Vote.created_at.label("event_at"),
            literal("unavailable", String).label("status"),
            literal("voted", String).label("event_kind"),
            literal(False, Boolean).label("can_view"),
        )
        .join(Consultation, Consultation.id == Vote.consultation_id)
        .where(
            Vote.voter_id == account_id,
            Consultation.state != ConsultationState.open,
            ~has_outcome,
        )
    )


def list_participation_history(
    db: Session,
    account_id: uuid.UUID,
    limit: int,
    cursor: tuple[datetime, datetime, uuid.UUID] | None,
    now: datetime | None = None,
) -> ParticipationPage:
    """Return the current account's descending, snapshot-bounded participation page.

    ``cursor`` is ``(snapshot, event_at, consultation_id)`` decoded by ``decode_history_cursor``;
    ``None`` starts a fresh page with a new snapshot. Rows are scoped to ``account_id`` in every
    union branch before ordering/limiting, so no client-supplied identifier can widen the result.
    """
    if cursor is None:
        snapshot = _as_naive_utc(now or utcnow())
    else:
        snapshot, _event_at, _cid = cursor

    combined = union_all(
        _open_vote_select(account_id),
        _outcome_select(account_id),
        _terminal_vote_select(account_id),
    ).subquery()

    statement = select(
        combined.c.consultation_id,
        combined.c.event_at,
        combined.c.status,
        combined.c.event_kind,
        combined.c.can_view,
    ).where(combined.c.event_at <= snapshot)

    if cursor is not None:
        _snapshot, cursor_event_at, cursor_id = cursor
        statement = statement.where(
            or_(
                combined.c.event_at < cursor_event_at,
                and_(
                    combined.c.event_at == cursor_event_at,
                    combined.c.consultation_id < cursor_id,
                ),
            )
        )

    statement = statement.order_by(
        combined.c.event_at.desc(), combined.c.consultation_id.desc()
    ).limit(limit + 1)

    rows = db.execute(statement).all()

    page_rows = rows[:limit]
    items: list[ParticipationItem] = []
    anomalies = 0
    for row in page_rows:
        status: ParticipationStatus = row.status
        if status == "unavailable":
            anomalies += 1
        items.append(
            ParticipationItem(
                consultation_id=str(row.consultation_id),
                status=status,
                event_kind=cast_event_kind(row.event_kind),
                event_at=_as_naive_utc(row.event_at),
                can_view=bool(row.can_view),
            )
        )

    if anomalies:
        logger.warning(
            "participation history: terminal vote anomalies detected count=%d", anomalies
        )

    next_cursor = None
    if len(rows) > limit and page_rows:
        last = page_rows[-1]
        next_cursor = encode_history_cursor(
            snapshot, last.event_at, uuid.UUID(str(last.consultation_id))
        )

    return ParticipationPage(items=items, next_cursor=next_cursor)


def cast_event_kind(value: str) -> ParticipationEventKind:
    """Normalize the union's literal event kind to its typed contract."""
    return "finalized" if value == "finalized" else "voted"
