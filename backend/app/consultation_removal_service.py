"""Restricted, command-only administrator removal of one open consultation (RF-32).

The caller's deployment access is the authority boundary. This service receives a validated
server-side operator label and explicit operation payload, locks the consultation row, proves exact
replays, and commits the minimal audit, vote removal, RF-37 marker, terminal sanitization and
``removed`` lifecycle as one database unit. It never touches the filesystem or exposes an HTTP
surface.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.consultation_service import ConsultationConflictError, ConsultationUnavailableError
from app.models import (
    REMOVAL_OPERATOR_ID_MAX_LENGTH,
    Consultation,
    ConsultationFinalization,
    ConsultationOutcome,
    ConsultationRemoval,
    ConsultationState,
    Vote,
)
from app.photo_erasure_service import mark_media_for_erasure, sanitize_terminal_content
from app.photo_service import utcnow

logger = logging.getLogger(__name__)

ALLOWED_REMOVAL_REASONS = frozenset(
    {"rights_or_privacy", "safety_or_abuse", "vote_integrity", "other"}
)


class RemovalInvalidError(Exception):
    """A service input is outside the fixed RF-32 command contract."""


class RemovalConsistencyError(Exception):
    """Persisted data cannot safely be handled by the open-only removal operation."""


@dataclass(frozen=True)
class RemovalResult:
    consultation_id: uuid.UUID
    operation_id: uuid.UUID
    previous_state: str
    reason_code: str
    removed_at: datetime
    classification: str
    votes_removed: int
    images_marked: int


def _validate_service_input(expected_state: str, operator_id: str, reason_code: str) -> None:
    if expected_state != ConsultationState.open.value:
        raise RemovalInvalidError("expected_state must be open")
    if not operator_id or len(operator_id) > REMOVAL_OPERATOR_ID_MAX_LENGTH:
        raise RemovalInvalidError("operator_id is invalid")
    if reason_code not in ALLOWED_REMOVAL_REASONS:
        raise RemovalInvalidError("reason_code is invalid")


def _matches_exact_replay(
    removal: ConsultationRemoval,
    operation_id: uuid.UUID,
    operator_id: str,
    reason_code: str,
) -> bool:
    return (
        removal.operation_id == operation_id
        and removal.operator_id == operator_id
        and removal.reason_code == reason_code
        and removal.previous_state == ConsultationState.open.value
    )


def _result(removal: ConsultationRemoval, classification: str) -> RemovalResult:
    return RemovalResult(
        consultation_id=removal.consultation_id,
        operation_id=removal.operation_id,
        previous_state=removal.previous_state,
        reason_code=removal.reason_code,
        removed_at=removal.removed_at,
        classification=classification,
        votes_removed=0,
        images_marked=0,
    )


def _log_result(result: RemovalResult) -> None:
    logger.info(
        "restricted removal: classification=%s consultation_id=%s operation_id=%s "
        "previous_state=%s reason_code=%s votes_removed=%s images_marked=%s",
        result.classification,
        result.consultation_id,
        result.operation_id,
        result.previous_state,
        result.reason_code,
        result.votes_removed,
        result.images_marked,
    )


def _raise_conflict(consultation_id: uuid.UUID, operation_id: uuid.UUID) -> None:
    logger.info(
        "restricted removal: classification=conflict consultation_id=%s operation_id=%s",
        consultation_id,
        operation_id,
    )
    raise ConsultationConflictError()


def remove_consultation(
    db: Session,
    consultation_id: uuid.UUID,
    operation_id: uuid.UUID,
    expected_state: str,
    operator_id: str,
    reason_code: str,
    now: datetime | None = None,
) -> RemovalResult:
    """Remove one open consultation or return its proven exact replay.

    Missing targets are unavailable. Every terminal or mismatched replay is a conflict. Unexpected
    failures roll back the transaction so the command cannot leave in-session partial markers.
    """
    _validate_service_input(expected_state, operator_id, reason_code)
    current = now or utcnow()

    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one_or_none()
    if consultation is None:
        raise ConsultationUnavailableError()

    target_removal = db.get(ConsultationRemoval, consultation_id)
    operation_removal = db.scalar(
        select(ConsultationRemoval).where(ConsultationRemoval.operation_id == operation_id)
    )

    if consultation.state == ConsultationState.removed:
        if (
            target_removal is not None
            and operation_removal is not None
            and operation_removal.consultation_id == consultation_id
            and _matches_exact_replay(target_removal, operation_id, operator_id, reason_code)
        ):
            result = _result(target_removal, "replay")
            _log_result(result)
            return result
        _raise_conflict(consultation_id, operation_id)

    if consultation.state != ConsultationState.open:
        _raise_conflict(consultation_id, operation_id)

    if target_removal is not None or operation_removal is not None:
        _raise_conflict(consultation_id, operation_id)

    has_finalization = db.get(ConsultationFinalization, consultation_id) is not None
    has_outcome = (
        db.scalar(
            select(ConsultationOutcome.id)
            .where(ConsultationOutcome.consultation_id == consultation_id)
            .limit(1)
        )
        is not None
    )
    if has_finalization or has_outcome:
        logger.error(
            "restricted removal: classification=consistency_error consultation_id=%s "
            "operation_id=%s",
            consultation_id,
            operation_id,
        )
        raise RemovalConsistencyError("open consultation has finalized result records")

    try:
        mark = mark_media_for_erasure(db, consultation, current)
        vote_count = db.scalar(
            select(func.count()).select_from(Vote).where(Vote.consultation_id == consultation_id)
        )
        votes_removed = int(vote_count or 0)
        db.execute(delete(Vote).where(Vote.consultation_id == consultation_id))
        sanitize_terminal_content(consultation)

        removal = ConsultationRemoval(
            consultation_id=consultation_id,
            operation_id=operation_id,
            removed_at=current,
            operator_id=operator_id,
            reason_code=reason_code,
            previous_state=ConsultationState.open.value,
        )
        db.add(removal)
        consultation.state = ConsultationState.removed
        db.commit()
    except IntegrityError:
        db.rollback()
        collision = db.scalar(
            select(ConsultationRemoval).where(ConsultationRemoval.operation_id == operation_id)
        )
        if collision is not None:
            _raise_conflict(consultation_id, operation_id)
        logger.error(
            "restricted removal: classification=error consultation_id=%s operation_id=%s",
            consultation_id,
            operation_id,
        )
        raise
    except Exception:
        db.rollback()
        logger.error(
            "restricted removal: classification=error consultation_id=%s operation_id=%s",
            consultation_id,
            operation_id,
        )
        raise

    result = RemovalResult(
        consultation_id=consultation_id,
        operation_id=operation_id,
        previous_state=ConsultationState.open.value,
        reason_code=reason_code,
        removed_at=current,
        classification="first",
        votes_removed=votes_removed,
        images_marked=mark.marked_images,
    )
    _log_result(result)
    return result
