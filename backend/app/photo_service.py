import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.imaging import ImageProcessingError, process_image
from app.models import (
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.storage import PhotoStorage, StorageError

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _is_expired(lease_expires_at: datetime, now: datetime) -> bool:
    return _as_naive_utc(lease_expires_at) <= _as_naive_utc(now)


class PhotoError(Exception):
    code = "photo_error"
    status_code = 400

    def __init__(self) -> None:
        super().__init__(self.code)


class NotFoundError(PhotoError):
    code = "not_found"
    status_code = 404


class InactiveSessionError(PhotoError):
    code = "session_inactive"
    status_code = 409


class PhotoLimitReachedError(PhotoError):
    code = "photo_limit_reached"
    status_code = 409


class AttemptInProgressError(PhotoError):
    code = "attempt_in_progress"
    status_code = 409


class AttemptConflictError(PhotoError):
    code = "attempt_conflict"
    status_code = 409


class InvalidAttemptError(PhotoError):
    code = "invalid_attempt"
    status_code = 422


class InputTooLargeError(PhotoError):
    code = "input_too_large"
    status_code = 413


class TooManyPixelsError(PhotoError):
    code = "too_many_pixels"
    status_code = 422


class UnsupportedFormatError(PhotoError):
    code = "unsupported_format"
    status_code = 422


class AnimatedInputError(PhotoError):
    code = "animated_input"
    status_code = 422


class InvalidImageError(PhotoError):
    code = "invalid_image"
    status_code = 422


class ImageProcessingFailedError(PhotoError):
    code = "image_processing_failed"
    status_code = 422


class ImageUnavailableError(PhotoError):
    code = "unavailable"
    status_code = 503


class PublicationInvalidError(PhotoError):
    code = "publication_invalid"
    status_code = 409


_PROCESSING_ERRORS: dict[str, type[PhotoError]] = {
    "too_many_pixels": TooManyPixelsError,
    "unsupported_format": UnsupportedFormatError,
    "animated_input": AnimatedInputError,
    "invalid_image": InvalidImageError,
    "image_processing_failed": ImageProcessingFailedError,
}


@dataclass(frozen=True)
class ReadyImage:
    id: uuid.UUID
    width: int
    height: int


def _get_session_for_owner(
    db: Session,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    *,
    lock: bool = False,
) -> PhotoUploadSession:
    statement = select(PhotoUploadSession).where(PhotoUploadSession.id == session_id)
    if lock:
        statement = statement.with_for_update()
    row = db.scalar(statement)
    if row is None or row.account_id != account_id:
        raise NotFoundError()
    return row


def _get_active_session(
    db: Session, account_id: uuid.UUID, session_id: uuid.UUID, now: datetime
) -> PhotoUploadSession:
    row = _get_session_for_owner(db, account_id, session_id, lock=True)
    if row.state != PhotoUploadSessionState.active or _is_expired(row.lease_expires_at, now):
        raise InactiveSessionError()
    return row


def create_upload_session(
    db: Session, account_id: uuid.UUID, now: datetime | None = None
) -> PhotoUploadSession:
    settings = get_settings()
    current = now or utcnow()
    row = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.active,
        lease_expires_at=current + timedelta(seconds=settings.photo_lease_seconds),
    )
    db.add(row)
    db.commit()
    return row


def renew_upload_session(
    db: Session, account_id: uuid.UUID, session_id: uuid.UUID, now: datetime | None = None
) -> PhotoUploadSession:
    settings = get_settings()
    current = now or utcnow()
    row = _get_session_for_owner(db, account_id, session_id, lock=True)
    if row.state != PhotoUploadSessionState.active or _is_expired(row.lease_expires_at, current):
        raise InactiveSessionError()
    row.lease_expires_at = current + timedelta(seconds=settings.photo_lease_seconds)
    db.commit()
    return row


def discard_upload_session(
    db: Session, account_id: uuid.UUID, session_id: uuid.UUID, now: datetime | None = None
) -> None:
    current = now or utcnow()
    row = _get_session_for_owner(db, account_id, session_id, lock=True)
    if row.state == PhotoUploadSessionState.active:
        row.state = PhotoUploadSessionState.discarded
        row.discarded_at = current
        row.lease_expires_at = current
        _revoke_images(db, session_id, current)
    db.commit()


def remove_image(
    db: Session,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    image_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    current = now or utcnow()
    _get_session_for_owner(db, account_id, session_id, lock=True)
    row = db.get(PhotoUploadImage, image_id)
    if row is None or row.upload_session_id != session_id:
        raise NotFoundError()
    if row.state in (PhotoImageState.ready, PhotoImageState.pending):
        row.state = PhotoImageState.revoked
        row.deletion_requested_at = current
        row.deletion_completed_at = None
    db.commit()


def _revoke_images(db: Session, session_id: uuid.UUID, now: datetime) -> int:
    rows = db.scalars(
        select(PhotoUploadImage).where(
            PhotoUploadImage.upload_session_id == session_id,
            PhotoUploadImage.state.in_((PhotoImageState.ready, PhotoImageState.pending)),
        )
    ).all()
    for row in rows:
        row.state = PhotoImageState.revoked
        row.deletion_requested_at = now
        row.deletion_completed_at = None
    return len(rows)


def read_image(
    db: Session,
    storage: PhotoStorage,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    image_id: uuid.UUID,
    now: datetime | None = None,
) -> tuple[bytes, str]:
    _get_active_session(db, account_id, session_id, now or utcnow())
    row = db.get(PhotoUploadImage, image_id)
    if row is None or row.upload_session_id != session_id:
        raise NotFoundError()
    if row.state != PhotoImageState.ready:
        raise NotFoundError()
    if row.storage_key is None:
        logger.error(
            "ready photo image has no storage key: image_id=%s session_id=%s",
            row.id,
            session_id,
        )
        raise ImageUnavailableError()
    try:
        content = storage.read_normalized(row.storage_key)
    except StorageError:
        logger.error(
            "ready photo image bytes are missing: image_id=%s session_id=%s",
            row.id,
            session_id,
        )
        raise ImageUnavailableError() from None
    return content, "image/jpeg"


def _stream_to_file(file: BinaryIO, path: Path, max_input_bytes: int) -> None:
    total = 0
    with path.open("wb") as out:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_input_bytes:
                raise InputTooLargeError()
            out.write(chunk)


def upload_image(
    db: Session,
    storage: PhotoStorage,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    attempt_id: uuid.UUID,
    file: BinaryIO,
    now: datetime | None = None,
) -> ReadyImage:
    settings = get_settings()
    current = now or utcnow()

    session_row = db.execute(
        select(PhotoUploadSession).where(PhotoUploadSession.id == session_id).with_for_update()
    ).scalar_one_or_none()
    if session_row is None or session_row.account_id != account_id:
        raise NotFoundError()
    if session_row.state != PhotoUploadSessionState.active or _is_expired(
        session_row.lease_expires_at, current
    ):
        raise InactiveSessionError()

    existing = db.scalar(
        select(PhotoUploadImage).where(
            PhotoUploadImage.upload_session_id == session_id,
            PhotoUploadImage.attempt_id == attempt_id,
        )
    )
    if existing is not None:
        if existing.state == PhotoImageState.ready:
            return ReadyImage(
                id=existing.id, width=existing.width or 0, height=existing.height or 0
            )
        if existing.state == PhotoImageState.pending:
            raise AttemptInProgressError()
        raise AttemptConflictError()

    in_flight = db.scalar(
        select(func.count())
        .select_from(PhotoUploadImage)
        .where(
            PhotoUploadImage.upload_session_id == session_id,
            PhotoUploadImage.state.in_((PhotoImageState.pending, PhotoImageState.ready)),
        )
    )
    if in_flight is not None and in_flight >= settings.consultation_max_photos:
        raise PhotoLimitReachedError()

    image_row = PhotoUploadImage(
        upload_session_id=session_id, attempt_id=attempt_id, state=PhotoImageState.pending
    )
    db.add(image_row)

    tmp_path = storage.new_tmp_path()
    try:
        _stream_to_file(file, tmp_path, settings.photo_max_input_bytes)
        data = tmp_path.read_bytes()
        normalized = process_image(data, settings.photo_max_pixels, settings.photo_max_output_edge)
        key = storage.new_key()
        storage.write_normalized(key, normalized.content)
        image_row.state = PhotoImageState.ready
        image_row.storage_key = key
        image_row.width = normalized.width
        image_row.height = normalized.height
        image_row.byte_length = len(normalized.content)
        db.commit()
        return ReadyImage(id=image_row.id, width=normalized.width, height=normalized.height)
    except InputTooLargeError as exc:
        _persist_failed(db, image_row)
        raise exc
    except ImageProcessingError as exc:
        _persist_failed(db, image_row)
        raise _PROCESSING_ERRORS.get(exc.code, ImageProcessingFailedError)() from exc
    except PhotoError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("unexpected upload failure: session_id=%s", session_id)
        raise ImageProcessingFailedError() from exc
    finally:
        try:
            storage.delete_tmp(tmp_path)
        except StorageError:
            logger.exception(
                "temporary upload cleanup failed: session_id=%s",
                session_id,
            )


def _persist_failed(db: Session, image_row: PhotoUploadImage) -> None:
    image_row.state = PhotoImageState.failed
    try:
        db.commit()
    except Exception:
        db.rollback()


def validate_publication_images(
    db: Session,
    storage: PhotoStorage,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    ordered_ids: list[uuid.UUID],
    now: datetime | None = None,
) -> list[PhotoUploadImage]:
    settings = get_settings()
    current = now or utcnow()

    session_row = db.execute(
        select(PhotoUploadSession).where(PhotoUploadSession.id == session_id).with_for_update()
    ).scalar_one_or_none()
    if session_row is None or session_row.account_id != account_id:
        raise NotFoundError()
    if session_row.state != PhotoUploadSessionState.active or _is_expired(
        session_row.lease_expires_at, current
    ):
        raise InactiveSessionError()

    if len(ordered_ids) != len(set(ordered_ids)):
        raise PublicationInvalidError()
    if not (
        settings.consultation_min_photos <= len(ordered_ids) <= settings.consultation_max_photos
    ):
        raise PublicationInvalidError()

    images: list[PhotoUploadImage] = []
    for image_id in ordered_ids:
        row = db.get(PhotoUploadImage, image_id)
        if row is None or row.upload_session_id != session_id:
            raise NotFoundError()
        if row.state != PhotoImageState.ready or row.storage_key is None:
            raise PublicationInvalidError()
        if not storage.exists(row.storage_key):
            logger.error(
                "publication photo bytes are missing: image_id=%s session_id=%s",
                row.id,
                session_id,
            )
            raise PublicationInvalidError()
        images.append(row)
    return images
