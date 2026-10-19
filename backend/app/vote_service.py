"""Viewer-scoped immutable vote persistence and submission (RF-16).

A vote is one immutable selection of a consultation option by a registered non-owner account.
This module owns the persistence boundary: it authorizes the current consultation state inside the
same transaction as the insert, serializes submissions with a PostgreSQL consultation row lock, and
returns only the current account's recorded option. It never computes or returns aggregate or
other-voter information (RF-18 owns author aggregates).

Reads authorize against the latest committed state but do not lock; submission locks the
consultation row ``FOR UPDATE`` before re-reading state so a late vote cannot commit on the far side
of a terminal transition (DEC-033). The ``(consultation_id, voter_id)`` unique constraint and the
composite ``(consultation_id, consultation_photo_id)`` foreign key remain the database backstops.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.consultation_access import AccessOperation, can_access
from app.consultation_service import (
    ConsultationUnavailableError,
    _build_snapshot,
    _link_verifier,
)
from app.models import Consultation, ConsultationPhoto, Vote


class VoteAlreadyRecordedError(Exception):
    """A different option already won for this account/consultation; it is never overwritten."""

    code = "vote_already_recorded"
    status_code = 409


class VoteInvalidSelectionError(Exception):
    """The requested option does not belong to the authorized consultation."""

    code = "invalid_selection"
    status_code = 422


@dataclass(frozen=True)
class VoteRead:
    status: str
    photo_id: str | None


@dataclass(frozen=True)
class VoteSubmit:
    status: str
    photo_id: str
    created: bool


def _authorize_vote(
    consultation: Consultation, account_id: uuid.UUID, presented_token: str | None
) -> None:
    snapshot = _build_snapshot(consultation)
    decision = can_access(
        snapshot,
        str(account_id),
        presented_token,
        AccessOperation.vote,
        _link_verifier(get_settings().private_link_secret),
    )
    if not decision.allowed:
        raise ConsultationUnavailableError()


def read_my_vote(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    presented_token: str | None,
) -> VoteRead:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ConsultationUnavailableError()
    _authorize_vote(consultation, account_id, presented_token)

    vote = db.scalar(
        select(Vote).where(Vote.consultation_id == consultation_id, Vote.voter_id == account_id)
    )
    if vote is None:
        return VoteRead(status="not_voted", photo_id=None)
    return VoteRead(status="voted", photo_id=str(vote.consultation_photo_id))


def submit_vote(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    presented_token: str | None,
    photo_id: uuid.UUID,
) -> VoteSubmit:
    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one_or_none()
    if consultation is None:
        raise ConsultationUnavailableError()
    _authorize_vote(consultation, account_id, presented_token)

    existing = db.scalar(
        select(Vote).where(Vote.consultation_id == consultation_id, Vote.voter_id == account_id)
    )
    if existing is not None:
        if existing.consultation_photo_id == photo_id:
            return VoteSubmit(
                status="voted", photo_id=str(existing.consultation_photo_id), created=False
            )
        raise VoteAlreadyRecordedError()

    option = db.scalar(
        select(ConsultationPhoto).where(
            ConsultationPhoto.id == photo_id,
            ConsultationPhoto.consultation_id == consultation_id,
        )
    )
    if option is None:
        raise VoteInvalidSelectionError()

    db.add(
        Vote(
            consultation_id=consultation_id,
            voter_id=account_id,
            consultation_photo_id=photo_id,
        )
    )
    db.commit()
    return VoteSubmit(status="voted", photo_id=str(photo_id), created=True)
