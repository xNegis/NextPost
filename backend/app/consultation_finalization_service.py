"""Author-only atomic finalization and final-choice declaration (RF-19/RF-20).

This module is the product boundary for the single indivisible operation that ends an open
consultation: the authenticated author declares one, several or no stable option and the winning
transaction freezes the valid votes, writes the definitive photo-free snapshot and the private
participant outcomes, deletes the raw votes, schedules RF-37 erasure, sanitizes forbidden content
and commits ``finalized`` once.

Serialization uses the same consultation row lock as voting and RF-13, so first commit wins without
priority among finalization, open deletion and restricted removal. Exact retries are proven by a
client-generated operation UUID plus a canonical payload fingerprint; a different payload or a new
operation against a terminal consultation is a safe conflict.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.consultation_service import (
    ConsultationConflictError,
    ConsultationError,
    ConsultationUnavailableError,
)
from app.finalization_summary import FinalizedResultSummary, build_finalized_summary
from app.models import (
    Consultation,
    ConsultationFinalization,
    ConsultationFinalOptionCount,
    ConsultationFinalSelection,
    ConsultationOutcome,
    ConsultationPhoto,
    ConsultationState,
    FinalizationOutcome,
    Vote,
)
from app.photo_erasure_service import mark_media_for_erasure, sanitize_terminal_content
from app.photo_service import _as_naive_utc, utcnow

logger = logging.getLogger(__name__)

_FINALIZE_FINGERPRINT_VERSION = "finalize-v1"


class FinalizationInvalidError(ConsultationError):
    """The declared selection is structurally or semantically invalid (field-safe 422)."""

    code = "invalid_declaration"
    status_code = 422


@dataclass(frozen=True)
class FinalizationDeclaration:
    kind: Literal["selected", "none"]
    option_ids: tuple[uuid.UUID, ...]


@dataclass(frozen=True)
class FinalizeResult:
    consultation_id: uuid.UUID
    published_at: datetime
    classification: str
    summary: FinalizedResultSummary
    images_marked: int
    matched: int
    not_matched: int
    no_choice: int


def finalize_fingerprint(declaration: FinalizationDeclaration) -> str:
    """Return a versioned canonical digest over the declaration for exact-retry proof."""
    payload = json.dumps(
        [
            _FINALIZE_FINGERPRINT_VERSION,
            declaration.kind,
            sorted(str(option_id) for option_id in declaration.option_ids),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_options(db: Session, consultation_id: uuid.UUID) -> list[ConsultationPhoto]:
    return list(
        db.scalars(
            select(ConsultationPhoto)
            .where(ConsultationPhoto.consultation_id == consultation_id)
            .order_by(ConsultationPhoto.ordinal)
        ).all()
    )


def _validate_declaration(
    declaration: FinalizationDeclaration, options: list[ConsultationPhoto]
) -> set[uuid.UUID]:
    """Validate the declaration against the consultation's stable options.

    Returns the set of selected stable option IDs. Raises ``FinalizationInvalidError`` for an empty
    or duplicate ``selected`` set or for any referenced ID that is not one of the consultation's own
    options; a ``none`` declaration must carry no IDs.
    """
    if declaration.kind == "none":
        if declaration.option_ids:
            raise FinalizationInvalidError()
        return set()

    if not declaration.option_ids:
        raise FinalizationInvalidError()
    if len(set(declaration.option_ids)) != len(declaration.option_ids):
        raise FinalizationInvalidError()

    option_ids = {option.id for option in options}
    for option_id in declaration.option_ids:
        if option_id not in option_ids:
            raise FinalizationInvalidError()
    return set(declaration.option_ids)


def _log_first(result: FinalizeResult) -> None:
    logger.info(
        "finalization: classification=first consultation_id=%s total_votes=%s "
        "selected_count=%s matched=%s not_matched=%s no_choice=%s images_marked=%s",
        result.consultation_id,
        result.summary.total_votes,
        len(result.summary.selected_ordinals),
        result.matched,
        result.not_matched,
        result.no_choice,
        result.images_marked,
    )


def _log_replay(result: FinalizeResult) -> None:
    logger.info(
        "finalization: classification=replay consultation_id=%s total_votes=%s",
        result.consultation_id,
        result.summary.total_votes,
    )


def _log_conflict(consultation: Consultation) -> None:
    logger.info(
        "finalization: classification=conflict consultation_id=%s current_state=%s",
        consultation.id,
        consultation.state.value,
    )


def _log_error(consultation_id: uuid.UUID) -> None:
    logger.error(
        "finalization: classification=error consultation_id=%s",
        consultation_id,
    )


def _replay(db: Session, consultation: Consultation) -> FinalizeResult:
    summary = build_finalized_summary(db, consultation.id)
    assert summary is not None
    result = FinalizeResult(
        consultation_id=consultation.id,
        published_at=_as_naive_utc(consultation.published_at),
        classification="replay",
        summary=summary,
        images_marked=0,
        matched=0,
        not_matched=0,
        no_choice=0,
    )
    _log_replay(result)
    return result


def finalize_consultation(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    operation_id: uuid.UUID,
    declaration: FinalizationDeclaration,
    now: datetime | None = None,
) -> FinalizeResult:
    """Lock, authorize and perform an atomic finalization/declaration in one transaction.

    Returns a ``FinalizeResult`` for first success and exact replay; raises
    ``ConsultationUnavailableError`` for unknown/foreign/removed/author-deleted targets,
    ``ConsultationConflictError`` for a stale or mismatched terminal operation and
    ``FinalizationInvalidError`` for an invalid declaration on an authorized open consultation.
    """
    current = now or utcnow()
    fingerprint = finalize_fingerprint(declaration)

    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one_or_none()

    if consultation is None or consultation.owner_id != account_id:
        raise ConsultationUnavailableError()
    if consultation.state == ConsultationState.removed:
        raise ConsultationUnavailableError()
    if consultation.author_deleted_at is not None:
        raise ConsultationUnavailableError()

    lifecycle = consultation.state
    if lifecycle != ConsultationState.open:
        if lifecycle == ConsultationState.finalized:
            header = db.get(ConsultationFinalization, consultation_id)
            if (
                header is not None
                and header.operation_id == operation_id
                and header.payload_fingerprint == fingerprint
            ):
                return _replay(db, consultation)
        _log_conflict(consultation)
        raise ConsultationConflictError()

    options = _load_options(db, consultation.id)
    selected_ids = _validate_declaration(declaration, options)

    try:
        return _finalize_open(
            db, consultation, operation_id, fingerprint, declaration, selected_ids, options, current
        )
    except FinalizationInvalidError:
        raise
    except Exception:
        _log_error(consultation.id)
        raise


def _finalize_open(
    db: Session,
    consultation: Consultation,
    operation_id: uuid.UUID,
    fingerprint: str,
    declaration: FinalizationDeclaration,
    selected_ids: set[uuid.UUID],
    options: list[ConsultationPhoto],
    now: datetime,
) -> FinalizeResult:
    option_by_id = {option.id: option for option in options}

    votes = db.scalars(select(Vote).where(Vote.consultation_id == consultation.id)).all()

    counts: dict[uuid.UUID, int] = {option.id: 0 for option in options}
    outcomes: list[tuple[uuid.UUID, FinalizationOutcome]] = []
    matched = 0
    not_matched = 0
    no_choice = 0

    for vote in votes:
        if vote.consultation_photo_id not in option_by_id:
            raise RuntimeError("finalization encountered an unmappable vote")
        counts[vote.consultation_photo_id] += 1
        if declaration.kind == "none":
            outcome = FinalizationOutcome.no_choice
            no_choice += 1
        elif vote.consultation_photo_id in selected_ids:
            outcome = FinalizationOutcome.matched
            matched += 1
        else:
            outcome = FinalizationOutcome.not_matched
            not_matched += 1
        outcomes.append((vote.voter_id, outcome))

    total_votes = sum(counts.values())
    if total_votes != len(votes):
        raise RuntimeError("finalization vote counts do not reconcile")

    db.add(
        ConsultationFinalization(
            consultation_id=consultation.id,
            operation_id=operation_id,
            payload_fingerprint=fingerprint,
            finalized_at=now,
            total_votes=total_votes,
        )
    )
    # Flush the header first so the selection/count rows can reference it through their
    # ``fk_*_finalization`` foreign keys within the same transaction.
    db.flush()

    for option_id in sorted(selected_ids, key=lambda oid: option_by_id[oid].ordinal):
        option = option_by_id[option_id]
        db.add(
            ConsultationFinalSelection(
                consultation_id=consultation.id,
                consultation_photo_id=option.id,
                ordinal=option.ordinal,
            )
        )

    for option in options:
        db.add(
            ConsultationFinalOptionCount(
                consultation_id=consultation.id,
                consultation_photo_id=option.id,
                ordinal=option.ordinal,
                vote_count=counts[option.id],
            )
        )

    for voter_id, outcome in outcomes:
        db.add(
            ConsultationOutcome(
                consultation_id=consultation.id,
                voter_id=voter_id,
                outcome=outcome,
            )
        )

    db.flush()

    db.execute(delete(Vote).where(Vote.consultation_id == consultation.id))
    mark = mark_media_for_erasure(db, consultation, now)
    sanitize_terminal_content(consultation)
    consultation.state = ConsultationState.finalized
    db.commit()

    summary = build_finalized_summary(db, consultation.id)
    assert summary is not None
    result = FinalizeResult(
        consultation_id=consultation.id,
        published_at=_as_naive_utc(consultation.published_at),
        classification="first",
        summary=summary,
        images_marked=mark.marked_images,
        matched=matched,
        not_matched=not_matched,
        no_choice=no_choice,
    )
    _log_first(result)
    return result
