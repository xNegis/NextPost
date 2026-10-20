import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_engine, get_session_factory
from app.models import (
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_erasure_service import reconcile_terminal_media
from app.photo_service import _as_naive_utc, _revoke_images, utcnow
from app.storage import PhotoStorage, StorageError

logger = logging.getLogger(__name__)

_TMP_FILE_MAX_AGE_SECONDS = 3600

# Stable application-specific int64 identifying the NextPost photo-maintenance leader.
_MAINTENANCE_LOCK_KEY = 8231546371


@dataclass(frozen=True)
class CleanupReport:
    abandoned_sessions: int
    revoked_images: int
    deleted_files: int
    stale_attempts_removed: int
    orphan_files_removed: int
    tmp_files_removed: int
    pending_beyond_alert: int
    terminal_sessions_discovered: int = 0
    terminal_objects_requested: int = 0
    terminal_objects_deleted: int = 0
    terminal_objects_already_absent: int = 0
    terminal_objects_failed: int = 0
    terminal_sessions_completed: int = 0
    anomalies: int = 0
    busy: bool = False


class MaintenanceLock(Protocol):
    def acquire(self) -> bool: ...

    def release(self) -> None: ...


class NullMaintenanceLock:
    """Always-available leader for single-instance local runs and unit tests."""

    def acquire(self) -> bool:
        return True

    def release(self) -> None:
        return None


class PostgresAdvisoryMaintenanceLock:
    """PostgreSQL session advisory leader serializing filesystem reconciliation across replicas."""

    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self._connection: Any | None = None
        self._acquired = False

    def acquire(self) -> bool:
        self._connection = self._engine.connect()
        acquired = self._connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": _MAINTENANCE_LOCK_KEY}
        ).scalar_one()
        self._acquired = bool(acquired)
        return self._acquired

    def release(self) -> None:
        if self._connection is None:
            return
        try:
            if self._acquired:
                self._connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": _MAINTENANCE_LOCK_KEY}
                )
        finally:
            self._connection.close()
            self._connection = None
            self._acquired = False


def build_maintenance_lock() -> MaintenanceLock:
    settings = get_settings()
    if settings.database_url.startswith("postgresql"):
        return PostgresAdvisoryMaintenanceLock(get_engine())
    return NullMaintenanceLock()


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
        .join(PhotoUploadSession, PhotoUploadImage.upload_session_id == PhotoUploadSession.id)
        .where(
            PhotoUploadImage.state == PhotoImageState.revoked,
            PhotoUploadImage.deletion_requested_at.is_not(None),
            PhotoUploadImage.deletion_completed_at.is_(None),
            PhotoUploadSession.state != PhotoUploadSessionState.consumed,
        )
        .with_for_update(skip_locked=True, of=PhotoUploadImage)
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


def _log_report(report: CleanupReport) -> None:
    logger.info(
        "photo maintenance summary: abandoned_sessions=%s deleted_files=%s "
        "terminal_sessions_discovered=%s terminal_objects_requested=%s "
        "terminal_objects_deleted=%s terminal_objects_already_absent=%s "
        "terminal_objects_failed=%s terminal_sessions_completed=%s "
        "pending_beyond_alert=%s anomalies=%s",
        report.abandoned_sessions,
        report.deleted_files,
        report.terminal_sessions_discovered,
        report.terminal_objects_requested,
        report.terminal_objects_deleted,
        report.terminal_objects_already_absent,
        report.terminal_objects_failed,
        report.terminal_sessions_completed,
        report.pending_beyond_alert,
        report.anomalies,
    )
    if report.pending_beyond_alert > 0:
        logger.error(
            "photo deletion overdue beyond alert threshold: pending_beyond_alert=%s",
            report.pending_beyond_alert,
        )
    if report.anomalies > 0:
        logger.error(
            "photo maintenance anomalies require restricted operator handling: anomalies=%s",
            report.anomalies,
        )


def run_cleanup(
    db: Session,
    storage: PhotoStorage,
    now: datetime | None = None,
    lock: MaintenanceLock | None = None,
) -> CleanupReport:
    current = now or utcnow()
    maintenance_lock = lock if lock is not None else NullMaintenanceLock()
    if not maintenance_lock.acquire():
        maintenance_lock.release()
        logger.info("photo maintenance skipped: another pass holds the leader lock")
        return CleanupReport(
            abandoned_sessions=0,
            revoked_images=0,
            deleted_files=0,
            stale_attempts_removed=0,
            orphan_files_removed=0,
            tmp_files_removed=0,
            pending_beyond_alert=0,
            busy=True,
        )
    try:
        abandoned, revoked = _abandon_expired_sessions(db, current)
        # Make revocation visible before touching the filesystem. A concurrent read
        # must observe denied state before physical deletion starts.
        db.commit()

        terminal = reconcile_terminal_media(db, storage, current)

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
        anomalies = storage.count_normalized_anomalies() + terminal.anomalies
        pending = _pending_beyond_alert(db, current)

        report = CleanupReport(
            abandoned_sessions=abandoned,
            revoked_images=revoked,
            deleted_files=deleted_files,
            stale_attempts_removed=stale_attempts,
            orphan_files_removed=orphan_files,
            tmp_files_removed=tmp_files,
            pending_beyond_alert=pending,
            terminal_sessions_discovered=terminal.sessions_discovered,
            terminal_objects_requested=terminal.objects_requested,
            terminal_objects_deleted=terminal.objects_deleted,
            terminal_objects_already_absent=terminal.objects_already_absent,
            terminal_objects_failed=terminal.objects_failed,
            terminal_sessions_completed=terminal.sessions_completed,
            anomalies=anomalies,
        )
        _log_report(report)
        return report
    finally:
        maintenance_lock.release()


def _format_report(report: CleanupReport) -> str:
    return (
        f"cleanup: abandoned_sessions={report.abandoned_sessions} "
        f"deleted_files={report.deleted_files} "
        f"stale_attempts_removed={report.stale_attempts_removed} "
        f"orphan_files_removed={report.orphan_files_removed} "
        f"tmp_files_removed={report.tmp_files_removed} "
        f"pending_beyond_alert={report.pending_beyond_alert} "
        f"terminal_sessions_discovered={report.terminal_sessions_discovered} "
        f"terminal_objects_requested={report.terminal_objects_requested} "
        f"terminal_objects_deleted={report.terminal_objects_deleted} "
        f"terminal_objects_already_absent={report.terminal_objects_already_absent} "
        f"terminal_objects_failed={report.terminal_objects_failed} "
        f"terminal_sessions_completed={report.terminal_sessions_completed} "
        f"anomalies={report.anomalies}"
    )


def _exit_code(report: CleanupReport) -> int:
    if report.busy:
        return 2
    if report.pending_beyond_alert > 0 or report.anomalies > 0:
        return 1
    return 0


def main() -> None:
    settings = get_settings()
    storage = PhotoStorage(settings.photo_storage_root)
    storage.ensure_dirs()

    session_factory = get_session_factory()
    lock = build_maintenance_lock()
    with session_factory() as db:
        report = run_cleanup(db, storage, lock=lock)

    print(_format_report(report))
    code = _exit_code(report)
    if code == 2:
        print("cleanup: busy: another maintenance pass holds the leader lock")
    elif code == 1:
        if report.pending_beyond_alert > 0:
            print("cleanup: photo deletion pending beyond alert threshold")
        if report.anomalies > 0:
            print("cleanup: anomalies require restricted operator handling")
    sys.exit(code)


if __name__ == "__main__":
    main()
