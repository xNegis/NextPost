"""Voluntary author deletion of an owned consultation (RF-13).

This module is the product boundary for a deliberate, irreversible author deletion. It serializes
with voting and every other terminal writer on the consultation row lock, proves ownership and the
author-confirmed expected state under that lock, resolves exact retries idempotently, and performs
the lifecycle-specific minimization in a single transaction.

- Open deletion calls RF-37's transaction-local ``mark_media_for_erasure``, removes every raw
  ``Vote`` without producing an outcome, sanitizes disallowed content, and writes canonical
  ``deleted`` plus ``author_deleted_at``.
- Finalized withdrawal retains lifecycle ``finalized``, preserves only the future DEC-023 minimum
  records, removes residual raw votes, sanitizes content/link capability and writes
  ``author_deleted_at``.

The database commit is the user-visible success boundary; physical file deletion is owned by RF-37
maintenance and can never reopen access.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.consultation_service import (
    ConsultationConflictError,
    ConsultationUnavailableError,
)
from app.models import Consultation, ConsultationState, Vote
from app.photo_erasure_service import mark_media_for_erasure, sanitize_terminal_content
from app.photo_service import utcnow

logger = logging.getLogger(__name__)

EXPECTED_STATES = ("open", "finalized")


@dataclass(frozen=True)
class DeletionOutcome:
    consultation_id: uuid.UUID
    previous_lifecycle: str
    classification: str
    votes_removed: int
    images_marked: int


def _remove_votes(db: Session, consultation_id: uuid.UUID) -> int:
    count = db.scalar(
        select(func.count()).select_from(Vote).where(Vote.consultation_id == consultation_id)
    )
    removed = int(count or 0)
    db.execute(delete(Vote).where(Vote.consultation_id == consultation_id))
    return removed


def _replay(consultation: Consultation) -> DeletionOutcome:
    """Report the original source lifecycle for an exact replay of a committed deletion.

    A deleted-and-marked row was originally ``open``; a finalized-and-marked row was originally
    ``finalized``. The current (terminal) lifecycle alone does not carry that source state.
    """
    if consultation.state == ConsultationState.deleted:
        previous_lifecycle = ConsultationState.open.value
    else:
        previous_lifecycle = ConsultationState.finalized.value
    outcome = DeletionOutcome(
        consultation_id=consultation.id,
        previous_lifecycle=previous_lifecycle,
        classification="replay",
        votes_removed=0,
        images_marked=0,
    )
    _log_outcome(outcome)
    return outcome


def _log_outcome(outcome: DeletionOutcome) -> None:
    logger.info(
        "author deletion: classification=%s consultation_id=%s previous_lifecycle=%s "
        "votes_removed=%s images_marked=%s",
        outcome.classification,
        outcome.consultation_id,
        outcome.previous_lifecycle,
        outcome.votes_removed,
        outcome.images_marked,
    )


def _log_conflict(consultation: Consultation, expected_state: str) -> None:
    logger.info(
        "author deletion: classification=conflict consultation_id=%s "
        "previous_lifecycle=%s expected_state=%s",
        consultation.id,
        consultation.state.value,
        expected_state,
    )


def _log_error(consultation_id: uuid.UUID) -> None:
    logger.error(
        "author deletion: classification=error consultation_id=%s",
        consultation_id,
    )


def delete_consultation(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    expected_state: str,
    now: datetime | None = None,
) -> DeletionOutcome:
    """Lock, authorize and perform a voluntary author deletion in one transaction.

    Returns a ``DeletionOutcome`` for first success and exact replay; raises
    ``ConsultationUnavailableError`` for unknown/foreign/removed targets and
    ``ConsultationConflictError`` for a stale or mismatched expected state.
    """
    current = now or utcnow()

    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one_or_none()

    if consultation is None or consultation.owner_id != account_id:
        raise ConsultationUnavailableError()

    lifecycle = consultation.state
    if lifecycle == ConsultationState.removed:
        raise ConsultationUnavailableError()

    marker = consultation.author_deleted_at

    if marker is not None:
        # A committed voluntary deletion already exists. An exact same-form retry is idempotent;
        # a request describing a different completed form is a safe conflict.
        if lifecycle == ConsultationState.deleted and expected_state == "open":
            return _replay(consultation)
        if lifecycle == ConsultationState.finalized and expected_state == "finalized":
            return _replay(consultation)
        _log_conflict(consultation, expected_state)
        raise ConsultationConflictError()

    if expected_state == "open":
        if lifecycle != ConsultationState.open:
            _log_conflict(consultation, expected_state)
            raise ConsultationConflictError()
        try:
            return _delete_open(db, consultation, current)
        except Exception:
            _log_error(consultation.id)
            raise

    if expected_state == "finalized":
        if lifecycle != ConsultationState.finalized:
            _log_conflict(consultation, expected_state)
            raise ConsultationConflictError()
        try:
            return _delete_finalized(db, consultation, current)
        except Exception:
            _log_error(consultation.id)
            raise

    _log_conflict(consultation, expected_state)
    raise ConsultationConflictError()


def _delete_open(db: Session, consultation: Consultation, now: datetime) -> DeletionOutcome:
    """Delete an open consultation: mark media, remove votes, sanitize, terminalize atomically."""
    mark = mark_media_for_erasure(db, consultation, now)
    votes_removed = _remove_votes(db, consultation.id)
    sanitize_terminal_content(consultation)
    consultation.state = ConsultationState.deleted
    consultation.author_deleted_at = now
    db.commit()

    outcome = DeletionOutcome(
        consultation_id=consultation.id,
        previous_lifecycle=ConsultationState.open.value,
        classification="first",
        votes_removed=votes_removed,
        images_marked=mark.marked_images,
    )
    _log_outcome(outcome)
    return outcome


def _delete_finalized(db: Session, consultation: Consultation, now: datetime) -> DeletionOutcome:
    """Withdraw a finalized consultation while preserving only future DEC-023 minimum records."""
    votes_removed = _remove_votes(db, consultation.id)
    sanitize_terminal_content(consultation)
    consultation.author_deleted_at = now
    db.commit()

    outcome = DeletionOutcome(
        consultation_id=consultation.id,
        previous_lifecycle=ConsultationState.finalized.value,
        classification="first",
        votes_removed=votes_removed,
        images_marked=0,
    )
    _log_outcome(outcome)
    return outcome
