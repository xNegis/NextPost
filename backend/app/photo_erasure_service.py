"""Database-first published-media erasure contract (RF-37).

A terminal consumer (RF-13 author deletion, RF-19/RF-20 finalization, restricted RF-32 removal)
locks the consultation row, persists its own terminal effects, and calls
``mark_media_for_erasure`` in the same transaction before its single commit. That marker never
commits, never chooses a lifecycle and never touches the filesystem; it only deactivates the
Private capability and normalizes every object in the unique consumed source session into durable
``revoked`` deletion-pending state.

After commit, maintenance (``cleanup.py``) calls ``reconcile_terminal_media`` to discover terminal
consultations that still retain a consumed source session, mark any remaining ready images revoked,
then delete and verify the absence of every exact object before detaching the stable option and
removing the visual/upload ledger. Access is revoked by the terminal commit and can never be
reopened by a storage failure.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_service import utcnow
from app.storage import PhotoStorage, StorageError

logger = logging.getLogger(__name__)

# DEC-023 terminal persistence allowlist. After a terminal consumer has persisted its permitted
# replacement data, a consultation may retain only identifiers, relevant dates/state, stable option
# ordinals/media-deletion markers, declared option IDs, aggregate counts and participant outcomes.
# RF-13 adds the single irreversible author-deletion marker (``author_deleted_at``) required to
# record a voluntary withdrawal without reopening the consultation. Every other stored field is
# disallowed and must be removed by the owning consumer through ``sanitize_terminal_content``.
# Absence from this list is not permission to keep data for analytics, debugging, moderation or
# models.
TERMINAL_CONTENT_ALLOWLIST = frozenset(
    {
        "id",
        "owner_id",
        "state",
        "published_at",
        "created_at",
        "updated_at",
        "author_deleted_at",
        "private_link_generation",
        "private_link_active",
    }
)

_TERMINAL_STATES = (
    ConsultationState.finalized,
    ConsultationState.deleted,
    ConsultationState.removed,
)


class ErasurePreconditionError(Exception):
    """The erasure marker was invoked outside its required locked/open/consumed context."""


@dataclass(frozen=True)
class ErasureMark:
    """Result of the transaction-local marker (no filesystem or commit side effect)."""

    session_id: uuid.UUID
    marked_images: int


@dataclass(frozen=True)
class TerminalMediaReport:
    sessions_discovered: int
    objects_requested: int
    objects_deleted: int
    objects_already_absent: int
    objects_failed: int
    sessions_completed: int
    anomalies: int = 0


def _source_session_images(db: Session, session_id: uuid.UUID) -> list[PhotoUploadImage]:
    return list(
        db.scalars(
            select(PhotoUploadImage).where(PhotoUploadImage.upload_session_id == session_id)
        ).all()
    )


def _mark_session_images(db: Session, session_id: uuid.UUID, now: datetime) -> int:
    """Durably revoke every remaining ready/pending image in one source session.

    Existing revoked work is preserved; a legacy ``deleted`` row keeps its completion timestamp so
    reconciliation can re-verify it. ``failed`` rows (no bytes) are left for removal. Returns the
    number of images newly marked revoked.
    """
    images = _source_session_images(db, session_id)
    marked = 0
    for image in images:
        if image.state in (PhotoImageState.ready, PhotoImageState.pending):
            image.state = PhotoImageState.revoked
            image.deletion_requested_at = now
            image.deletion_completed_at = None
            marked += 1
        elif image.state == PhotoImageState.revoked:
            if image.deletion_requested_at is None:
                image.deletion_requested_at = now
            image.deletion_completed_at = None
        elif image.state == PhotoImageState.deleted and image.deletion_completed_at is None:
            image.deletion_completed_at = now
    return marked


def _require_consumed_session(db: Session, consultation: Consultation) -> PhotoUploadSession:
    if consultation.source_session_id is None:
        raise ErasurePreconditionError("consultation has no source session")
    session = db.get(PhotoUploadSession, consultation.source_session_id)
    if session is None:
        raise ErasurePreconditionError("source session missing")
    if session.account_id != consultation.owner_id:
        raise ErasurePreconditionError("source session belongs to another account")
    if session.state != PhotoUploadSessionState.consumed:
        raise ErasurePreconditionError("source session is not consumed")
    return session


def mark_media_for_erasure(
    db: Session, consultation: Consultation, now: datetime | None = None
) -> ErasureMark:
    """Mark the complete unique consumed source session for deletion inside a terminal transaction.

    The caller must already hold the consultation row lock (``FOR UPDATE``), have re-read the
    current lifecycle and persisted its own operation data. This function requires an ``open``
    consultation with a unique consumed source session, sets ``private_link_active = false`` as
    defence in depth, marks every ready/pending image revoked, and performs no commit and no
    filesystem I/O.
    """
    if consultation.state != ConsultationState.open:
        raise ErasurePreconditionError("consultation is not open")

    current = now or utcnow()
    session = _require_consumed_session(db, consultation)

    consultation.private_link_active = False
    marked = _mark_session_images(db, session.id, current)
    return ErasureMark(session_id=session.id, marked_images=marked)


def sanitize_terminal_content(consultation: Consultation) -> None:
    """Remove disallowed content once the owning consumer has persisted its permitted replacement.

    This is an explicit DEC-023 allowlist seam, not generic ORM deletion. It nulls question,
    context, audience and the publication fingerprint and resets the Private link capability to its
    non-capability value. RF-13/RF-19/RF-20 and restricted RF-32 call it inside their own terminal
    transaction after producing any permitted outcome/aggregate data; RF-37 never invents that data.
    """
    consultation.question = None
    consultation.context = None
    consultation.audience = None
    consultation.fingerprint = None
    consultation.private_link_generation = 0
    consultation.private_link_active = False


def _detach_photo(db: Session, image_id: uuid.UUID, now: datetime) -> None:
    photo = db.scalar(select(ConsultationPhoto).where(ConsultationPhoto.image_id == image_id))
    if photo is not None:
        photo.image_id = None
        photo.media_deleted_at = now


def _record_failure(db: Session, image: PhotoUploadImage, now: datetime) -> None:
    image.deletion_attempts += 1
    image.last_deletion_error = "storage failure"
    logger.error(
        "published photo deletion failed: image_id=%s session_id=%s",
        image.id,
        image.upload_session_id,
    )


def _complete_image(
    db: Session, storage: PhotoStorage, image: PhotoUploadImage, now: datetime
) -> str:
    """Delete one exact validated key, verify absence, then detach and remove the visual ledger.

    Returns ``"deleted"`` when bytes were verified absent after a delete, ``"already_absent"`` when
    the object was already gone (or a keyless attempt) and removed idempotently, or ``"failed"``
    when the object still exists, storage errored or the key is invalid. Only a verified object is
    detached; failed keys retain their exact retry metadata.
    """
    key = image.storage_key
    if key is None:
        _detach_photo(db, image.id, now)
        db.delete(image)
        return "already_absent"

    try:
        present = storage.exists(key)
    except StorageError:
        _record_failure(db, image, now)
        return "failed"

    if not present:
        _detach_photo(db, image.id, now)
        db.delete(image)
        return "already_absent"

    try:
        storage.delete_normalized(key)
    except StorageError:
        _record_failure(db, image, now)
        return "failed"

    try:
        still_present = storage.exists(key)
    except StorageError:
        _record_failure(db, image, now)
        return "failed"

    if still_present:
        _record_failure(db, image, now)
        return "failed"

    _detach_photo(db, image.id, now)
    db.delete(image)
    return "deleted"


def _process_session(
    db: Session, storage: PhotoStorage, session_id: uuid.UUID, now: datetime
) -> tuple[int, int, int, int]:
    """Process every image in one consumed session; return (requested, deleted, absent, failed)."""
    requested = deleted = absent = failed = 0
    images = db.scalars(
        select(PhotoUploadImage)
        .where(PhotoUploadImage.upload_session_id == session_id)
        .with_for_update(skip_locked=True)
    ).all()
    for image in images:
        requested += 1
        result = _complete_image(db, storage, image, now)
        if result == "deleted":
            deleted += 1
        elif result == "already_absent":
            absent += 1
        else:
            failed += 1
    return requested, deleted, absent, failed


def _finalize_session(db: Session, session_id: uuid.UUID, consultation: Consultation) -> None:
    """Detach the consumed source session once every image/attempt is absent and removed."""
    db.flush()
    remaining = db.scalar(
        select(PhotoUploadImage.id).where(PhotoUploadImage.upload_session_id == session_id).limit(1)
    )
    if remaining is not None:
        return
    consultation.source_session_id = None
    session = db.get(PhotoUploadSession, session_id)
    if session is not None:
        db.delete(session)


def reconcile_terminal_media(
    db: Session, storage: PhotoStorage, now: datetime | None = None
) -> TerminalMediaReport:
    """Discover and converge terminal consultations that still retain consumed media.

    The discovery pass builds an explicit validated work list: only terminal consultations with a
    retained source session that exists, belongs to the same account and is ``consumed`` are
    processed. Missing, foreign-owner and non-consumed source sessions are counted as anomalies,
    reported for restricted handling, and are never physically processed or detached. Logical
    revocation is committed before any filesystem deletion. Every exact object is deleted and
    explicitly checked absent; partial/failed work retains its exact key and retry metadata so the
    next pass can continue.
    """
    current = now or utcnow()

    consultations = db.scalars(
        select(Consultation)
        .where(
            Consultation.state.in_(_TERMINAL_STATES),
            Consultation.source_session_id.is_not(None),
        )
        .with_for_update(skip_locked=True)
    ).all()

    sessions_discovered = len(consultations)
    work: list[tuple[Consultation, PhotoUploadSession]] = []
    anomalies = 0

    for consultation in consultations:
        assert consultation.source_session_id is not None
        session = db.get(PhotoUploadSession, consultation.source_session_id)
        if session is None:
            logger.error(
                "terminal consultation references a missing source session: consultation_id=%s",
                consultation.id,
            )
            anomalies += 1
            continue
        if session.account_id != consultation.owner_id:
            logger.error(
                "terminal consultation source session belongs to another account: "
                "consultation_id=%s session_id=%s",
                consultation.id,
                session.id,
            )
            anomalies += 1
            continue
        if session.state != PhotoUploadSessionState.consumed:
            logger.error(
                "terminal consultation source session is not consumed: "
                "consultation_id=%s session_id=%s",
                consultation.id,
                session.id,
            )
            anomalies += 1
            continue
        consultation.private_link_active = False
        _mark_session_images(db, session.id, current)
        work.append((consultation, session))

    # Logical revocation must be durable before any file is touched.
    db.commit()

    objects_requested = 0
    objects_deleted = 0
    objects_already_absent = 0
    objects_failed = 0
    sessions_completed = 0

    for consultation, session in work:
        requested, deleted, absent, failed = _process_session(db, storage, session.id, current)
        objects_requested += requested
        objects_deleted += deleted
        objects_already_absent += absent
        objects_failed += failed
        _finalize_session(db, session.id, consultation)
        if consultation.source_session_id is None:
            sessions_completed += 1

    db.commit()
    return TerminalMediaReport(
        sessions_discovered=sessions_discovered,
        objects_requested=objects_requested,
        objects_deleted=objects_deleted,
        objects_already_absent=objects_already_absent,
        objects_failed=objects_failed,
        sessions_completed=sessions_completed,
        anomalies=anomalies,
    )
