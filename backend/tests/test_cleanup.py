import io
import os
import uuid
from datetime import datetime, timedelta, timezone

from PIL import Image

from app.cleanup import CleanupReport, run_cleanup
from app.models import (
    Account,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_service import create_upload_session, discard_upload_session, upload_image
from app.storage import StorageError

T0 = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 30, 30)).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _account_id(db) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"a{suffix}@example.com",
        alias=f"User{suffix}",
        alias_canonical=f"user{suffix}",
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account.id


def _image_key(db, image_id: uuid.UUID) -> str:
    row = db.get(PhotoUploadImage, image_id)
    assert row is not None and row.storage_key is not None
    return row.storage_key


def _session_state(db, session_id: uuid.UUID) -> PhotoUploadSessionState:
    row = db.get(PhotoUploadSession, session_id)
    assert row is not None
    return row.state


def test_active_lease_is_not_purged(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )
        key = _image_key(db, image.id)

        report = run_cleanup(db, storage, now=T0 + timedelta(hours=23))

        assert _session_state(db, session.id) == PhotoUploadSessionState.active
        assert storage.exists(key) is True
        assert report.abandoned_sessions == 0


def test_expired_session_is_abandoned_and_images_deleted(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )
        key = _image_key(db, image.id)

        report = run_cleanup(db, storage, now=T0 + timedelta(hours=25))

        assert _session_state(db, session.id) == PhotoUploadSessionState.abandoned
        assert storage.exists(key) is False
        assert report.deleted_files == 1


def test_discarded_session_images_are_deleted(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )
        key = _image_key(db, image.id)

        discard_upload_session(db, account_id, session.id, now=T0)
        report = run_cleanup(db, storage, now=T0 + timedelta(hours=1))

        assert storage.exists(key) is False
        assert report.deleted_files == 1


def test_deletion_failure_is_retried(session_factory, storage, monkeypatch) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )
        key = _image_key(db, image.id)

        discard_upload_session(db, account_id, session.id, now=T0)

        def failing_delete(storage_key: str) -> None:
            raise StorageError("delete failed")

        monkeypatch.setattr(storage, "delete_normalized", failing_delete)
        run_cleanup(db, storage, now=T0 + timedelta(hours=1))
        assert storage.exists(key) is True

        monkeypatch.undo()
        report = run_cleanup(db, storage, now=T0 + timedelta(hours=2))
        assert storage.exists(key) is False
        assert report.deleted_files == 1


def test_orphan_files_are_swept(session_factory, storage) -> None:
    orphan_key = storage.new_key()
    storage.write_normalized(orphan_key, b"orphan")
    old = (T0 - timedelta(hours=2)).timestamp()
    os.utime(storage._normalized_path(orphan_key), (old, old))

    with session_factory() as db:
        report = run_cleanup(db, storage, now=T0)

    assert storage.exists(orphan_key) is False
    assert report.orphan_files_removed == 1


def test_recent_uncommitted_file_is_not_swept(session_factory, storage) -> None:
    recent_key = storage.new_key()
    storage.write_normalized(recent_key, b"in-flight")
    recent = (T0 - timedelta(minutes=5)).timestamp()
    os.utime(storage._normalized_path(recent_key), (recent, recent))

    with session_factory() as db:
        report = run_cleanup(db, storage, now=T0)

    assert storage.exists(recent_key) is True
    assert report.orphan_files_removed == 0


def test_pending_beyond_alert_is_reported(session_factory, storage, monkeypatch) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )

        discard_upload_session(db, account_id, session.id, now=T0)

        def failing_delete(storage_key: str) -> None:
            raise StorageError("delete failed")

        monkeypatch.setattr(storage, "delete_normalized", failing_delete)

        report = run_cleanup(db, storage, now=T0 + timedelta(hours=25))

        assert report.pending_beyond_alert == 1


def test_repeated_cleanup_is_idempotent(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )

        first = run_cleanup(db, storage, now=T0 + timedelta(hours=25))
        second = run_cleanup(db, storage, now=T0 + timedelta(hours=26))

        assert first.deleted_files == 1
        assert second.deleted_files == 0


def test_stale_failed_attempts_are_purged(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)

        db.add(
            PhotoUploadImage(
                upload_session_id=session.id,
                attempt_id=uuid.uuid4(),
                state=PhotoImageState.failed,
                updated_at=T0,
            )
        )
        db.commit()

        report: CleanupReport = run_cleanup(db, storage, now=T0 + timedelta(hours=25))

        assert report.stale_attempts_removed == 1
