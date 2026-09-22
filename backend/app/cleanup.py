import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session_factory
from app.models import (
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_service import _as_naive_utc, _revoke_images, utcnow
from app.storage import PhotoStorage, StorageError

logger = logging.getLogger(__name__)

_TMP_FILE_MAX_AGE_SECONDS = 3600


@dataclass(frozen=True)
class CleanupReport:
    abandoned_sessions: int
    revoked_images: int
    deleted_files: int
    stale_attempts_removed: int
    orphan_files_removed: int
    tmp_files_removed: int
    pending_beyond_alert: int


def _abandon_expired_sessions(db: Session, now: datetime) -> tuple[int, int]:
    rows = db.scalars(
        select(PhotoUploadSession)
        .where(PhotoUploadSession.state == PhotoUploadSessionState.active)
        .with_for_update(skip_locked=True)
    ).all()
    abandoned = 0
    revoked = 0
    for row in rows:
        if _as_naive_utc(row.lease_expires_at) <= _as_naive_utc(now):
            row.state = PhotoUploadSessionState.abandoned
            row.abandoned_at = now
            row.lease_expires_at = now
            revoked += _revoke_images(db, row.id, now)
            abandoned += 1
    return abandoned, revoked


def _record_deletion_failure(db: Session, row: PhotoUploadImage, now: datetime) -> None:
    settings = get_settings()
    row.deletion_attempts += 1
    row.last_deletion_error = "storage failure"
    age = _as_naive_utc(now) - _as_naive_utc(row.deletion_requested_at or now)
    if age >= timedelta(seconds=settings.photo_deletion_alert_seconds):
        logger.error(
            "photo deletion pending beyond alert threshold: image_id=%s session_id=%s",
            row.id,
            row.upload_session_id,
        )


def _retry_deletions(db: Session, storage: PhotoStorage, now: datetime) -> int:
    rows = db.scalars(
        select(PhotoUploadImage)
        .where(
            PhotoUploadImage.state == PhotoImageState.revoked,
            PhotoUploadImage.deletion_requested_at.is_not(None),
            PhotoUploadImage.deletion_completed_at.is_(None),
        )
        .with_for_update(skip_locked=True)
    ).all()
    deleted = 0
    for row in rows:
        if row.storage_key is None:
            row.state = PhotoImageState.deleted
            row.deletion_completed_at = now
            deleted += 1
            continue
        try:
            storage.delete_normalized(row.storage_key)
        except StorageError:
            _record_deletion_failure(db, row, now)
            continue
        if storage.exists(row.storage_key):
            _record_deletion_failure(db, row, now)
            continue
        row.state = PhotoImageState.deleted
        row.deletion_completed_at = now
        deleted += 1
    return deleted


def _purge_stale_attempts(db: Session, now: datetime) -> int:
    settings = get_settings()
    cutoff = now - timedelta(seconds=settings.photo_deletion_alert_seconds)
    rows = db.scalars(
        select(PhotoUploadImage).where(PhotoUploadImage.state == PhotoImageState.failed)
    ).all()
    removed = 0
    for row in rows:
        if _as_naive_utc(row.updated_at) < _as_naive_utc(cutoff):
            db.execute(delete(PhotoUploadImage).where(PhotoUploadImage.id == row.id))
            removed += 1
    return removed


def _valid_normalized_keys(db: Session) -> set[str]:
    rows = db.scalars(
        select(PhotoUploadImage.storage_key).where(
            PhotoUploadImage.state.in_((PhotoImageState.ready, PhotoImageState.revoked)),
            PhotoUploadImage.storage_key.is_not(None),
        )
    ).all()
    return {key for key in rows if key is not None}


def _pending_beyond_alert(db: Session, now: datetime) -> int:
    settings = get_settings()
    alert_age = timedelta(seconds=settings.photo_deletion_alert_seconds)
    rows = db.scalars(
        select(PhotoUploadImage).where(
            PhotoUploadImage.state == PhotoImageState.revoked,
            PhotoUploadImage.deletion_requested_at.is_not(None),
            PhotoUploadImage.deletion_completed_at.is_(None),
        )
    ).all()
    count = 0
    for row in rows:
        age = _as_naive_utc(now) - _as_naive_utc(row.deletion_requested_at or now)
        if age >= alert_age:
            count += 1
    return count


def run_cleanup(db: Session, storage: PhotoStorage, now: datetime | None = None) -> CleanupReport:
    current = now or utcnow()
    abandoned, revoked = _abandon_expired_sessions(db, current)
    # Make revocation visible before touching the filesystem. A concurrent read
    # must observe denied state before physical deletion starts.
    db.commit()

    deleted_files = _retry_deletions(db, storage, current)
    db.flush()
    stale_attempts = _purge_stale_attempts(db, current)
    db.commit()

    orphan_files = storage.sweep_normalized(
        _valid_normalized_keys(db),
        min_age_seconds=get_settings().photo_cleanup_interval_seconds,
        now_timestamp=current.timestamp(),
    )
    tmp_files = storage.sweep_tmp(_TMP_FILE_MAX_AGE_SECONDS, now_timestamp=current.timestamp())
    pending = _pending_beyond_alert(db, current)

    return CleanupReport(
        abandoned_sessions=abandoned,
        revoked_images=revoked,
        deleted_files=deleted_files,
        stale_attempts_removed=stale_attempts,
        orphan_files_removed=orphan_files,
        tmp_files_removed=tmp_files,
        pending_beyond_alert=pending,
    )


def main() -> None:
    settings = get_settings()
    storage = PhotoStorage(settings.photo_storage_root)
    storage.ensure_dirs()

    session_factory = get_session_factory()
    with session_factory() as db:
        report = run_cleanup(db, storage)

    print(
        f"cleanup: abandoned_sessions={report.abandoned_sessions} "
        f"deleted_files={report.deleted_files} "
        f"stale_attempts_removed={report.stale_attempts_removed} "
        f"orphan_files_removed={report.orphan_files_removed} "
        f"tmp_files_removed={report.tmp_files_removed} "
        f"pending_beyond_alert={report.pending_beyond_alert}"
    )
    if report.pending_beyond_alert > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
