import io
import logging
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.cleanup import _exit_code, run_cleanup
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_erasure_service import (
    ErasurePreconditionError,
    mark_media_for_erasure,
    reconcile_terminal_media,
    sanitize_terminal_content,
)
from app.storage import StorageError

T0 = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 30, 30)).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _account(db) -> uuid.UUID:
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


def _seed_consultation(
    db,
    account_id: uuid.UUID,
    *,
    audience: str = "public",
    image_count: int = 2,
    storage=None,
    leftover: bool = False,
):
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=T0,
    )
    db.add(session)
    db.flush()

    images = []
    for _ in range(image_count):
        key = uuid.uuid4().hex
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=key,
            width=10,
            height=10,
            byte_length=1,
        )
        db.add(image)
        db.flush()
        if storage is not None:
            storage.write_normalized(key, b"x")
        images.append(image)

    if leftover:
        db.add(
            PhotoUploadImage(
                upload_session_id=session.id,
                attempt_id=uuid.uuid4(),
                state=PhotoImageState.revoked,
                storage_key=uuid.uuid4().hex,
                deletion_requested_at=T0,
            )
        )
        db.flush()

    consultation = Consultation(
        owner_id=account_id,
        question="Q",
        context=None,
        audience=audience,
        state=ConsultationState.open,
        published_at=T0,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
        private_link_generation=1 if audience == "private" else 0,
        private_link_active=(audience == "private"),
    )
    db.add(consultation)
    db.flush()

    photos = []
    for ordinal, image in enumerate(images):
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo)

    db.commit()
    return consultation, session, images, photos


# --- Transaction-local marker ----------------------------------------------------------------


def test_marker_marks_ready_images_and_deactivates_private_link(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, session, images, _ = _seed_consultation(db, account_id, audience="private")
        image_ids = [image.id for image in images]
        cid = consultation.id

        locked = db.execute(
            select(Consultation).where(Consultation.id == cid).with_for_update()
        ).scalar_one()
        mark = mark_media_for_erasure(db, locked, now=T0)
        db.commit()

        assert mark.marked_images == 2
        for image_id in image_ids:
            row = db.get(PhotoUploadImage, image_id)
            assert row is not None
            assert row.state == PhotoImageState.revoked
            assert row.deletion_requested_at is not None
        assert db.get(Consultation, cid).private_link_active is False
        assert db.get(Consultation, cid).state == ConsultationState.open


def test_marker_performs_no_commit(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id)
        image_ids = [image.id for image in images]
        cid = consultation.id

        locked = db.execute(
            select(Consultation).where(Consultation.id == cid).with_for_update()
        ).scalar_one()
        mark_media_for_erasure(db, locked, now=T0)
        db.rollback()

    with session_factory() as db:
        for image_id in image_ids:
            assert db.get(PhotoUploadImage, image_id).state == PhotoImageState.ready
        assert db.get(Consultation, cid).private_link_active is False


def test_marker_marks_leftover_revoked_image(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, session, images, _ = _seed_consultation(db, account_id, leftover=True)
        cid = consultation.id

        locked = db.execute(
            select(Consultation).where(Consultation.id == cid).with_for_update()
        ).scalar_one()
        mark = mark_media_for_erasure(db, locked, now=T0)
        db.commit()

        assert mark.marked_images == 2
        rows = db.scalars(
            select(PhotoUploadImage).where(PhotoUploadImage.upload_session_id == session.id)
        ).all()
        assert {row.state for row in rows} == {PhotoImageState.revoked}


def test_marker_requires_open_state(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account_id)
        consultation.state = ConsultationState.deleted
        db.commit()

        with pytest.raises(ErasurePreconditionError):
            mark_media_for_erasure(db, consultation, now=T0)


def test_marker_requires_consumed_session(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, session, _, _ = _seed_consultation(db, account_id)
        session.state = PhotoUploadSessionState.active
        db.commit()

        with pytest.raises(ErasurePreconditionError):
            mark_media_for_erasure(db, consultation, now=T0)


def test_marker_rejects_foreign_session(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        other_id = _account(db)
        other_session = PhotoUploadSession(
            account_id=other_id,
            state=PhotoUploadSessionState.consumed,
            lease_expires_at=T0,
        )
        db.add(other_session)
        db.commit()

        consultation = Consultation(
            owner_id=account_id,
            question="Q",
            context=None,
            audience="public",
            state=ConsultationState.open,
            published_at=T0,
            source_session_id=other_session.id,
            fingerprint=uuid.uuid4().hex[:32],
        )
        db.add(consultation)
        db.commit()

        with pytest.raises(ErasurePreconditionError):
            mark_media_for_erasure(db, consultation, now=T0)


def test_marker_rejects_missing_source_session(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account_id)
        consultation.source_session_id = None

        with pytest.raises(ErasurePreconditionError):
            mark_media_for_erasure(db, consultation, now=T0)


# --- Reconciliation / verified physical deletion ---------------------------------------------


def test_reconcile_deletes_verifies_and_detaches(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, session, images, photos = _seed_consultation(db, account_id, storage=storage)
        image_ids = [image.id for image in images]
        photo_ids = [photo.id for photo in photos]
        keys = [image.storage_key for image in images]
        cid = consultation.id
        sid = session.id

        consultation.state = ConsultationState.deleted
        db.commit()

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.sessions_discovered == 1
        assert report.objects_requested == 2
        assert report.objects_deleted == 2
        assert report.objects_failed == 0
        assert report.sessions_completed == 1

    with session_factory() as db:
        for key in keys:
            assert storage.exists(key) is False
        for image_id in image_ids:
            assert db.get(PhotoUploadImage, image_id) is None
        for photo_id in photo_ids:
            photo = db.get(ConsultationPhoto, photo_id)
            assert photo is not None
            assert photo.image_id is None
            assert photo.media_deleted_at is not None
        assert db.get(PhotoUploadSession, sid) is None
        assert db.get(Consultation, cid).source_session_id is None


def test_reconcile_already_absent_is_idempotent(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id, storage=storage)
        image_ids = [image.id for image in images]
        keys = [image.storage_key for image in images]
        for key in keys:
            storage.delete_normalized(key)

        consultation.state = ConsultationState.deleted
        db.commit()

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.objects_already_absent == 2
        assert report.objects_deleted == 0
        assert report.sessions_completed == 1

    with session_factory() as db:
        for image_id in image_ids:
            assert db.get(PhotoUploadImage, image_id) is None


def test_reconcile_retains_failed_key_for_retry(session_factory, storage, monkeypatch) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id, storage=storage)
        image_ids = [image.id for image in images]
        keys = [image.storage_key for image in images]
        cid = consultation.id

        consultation.state = ConsultationState.deleted
        db.commit()

        def failing_delete(storage_key: str) -> None:
            raise StorageError("delete failed")

        monkeypatch.setattr(storage, "delete_normalized", failing_delete)

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.objects_failed == 2
        assert report.objects_deleted == 0
        assert report.sessions_completed == 0

    with session_factory() as db:
        for key in keys:
            assert storage.exists(key) is True
        for image_id in image_ids:
            row = db.get(PhotoUploadImage, image_id)
            assert row is not None
            assert row.state == PhotoImageState.revoked
            assert row.deletion_attempts == 1
            assert row.last_deletion_error == "storage failure"
        assert db.get(Consultation, cid).source_session_id is not None


def test_reconcile_partial_set_then_retry_converges(session_factory, storage, monkeypatch) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id, storage=storage)
        image_ids = [image.id for image in images]
        keys = [image.storage_key for image in images]
        cid = consultation.id
        sid = consultation.source_session_id

        consultation.state = ConsultationState.deleted
        db.commit()

        original_delete = storage.delete_normalized
        failing_key = keys[1]

        def selective_delete(storage_key: str) -> None:
            if storage_key == failing_key:
                raise StorageError("delete failed")
            original_delete(storage_key)

        monkeypatch.setattr(storage, "delete_normalized", selective_delete)
        first = reconcile_terminal_media(db, storage, now=T0)

        assert first.objects_deleted == 1
        assert first.objects_failed == 1
        assert first.sessions_completed == 0

        monkeypatch.undo()
        second = reconcile_terminal_media(db, storage, now=T0)

        assert second.objects_deleted == 1
        assert second.sessions_completed == 1

    with session_factory() as db:
        assert storage.exists(keys[0]) is False
        assert storage.exists(keys[1]) is False
        for image_id in image_ids:
            assert db.get(PhotoUploadImage, image_id) is None
        assert db.get(Consultation, cid).source_session_id is None
        assert db.get(PhotoUploadSession, sid) is None


def test_reconcile_invalid_key_fails_closed(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id, storage=storage)
        images[1].storage_key = "not-a-valid-key!!"
        good_key = images[0].storage_key
        bad_id = images[1].id
        consultation.state = ConsultationState.deleted
        db.commit()

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.objects_deleted == 1
        assert report.objects_failed == 1
        assert report.sessions_completed == 0

    with session_factory() as db:
        assert storage.exists(good_key) is False
        row = db.get(PhotoUploadImage, bad_id)
        assert row is not None
        assert row.state == PhotoImageState.revoked


def test_reconcile_leaves_other_consultations_intact(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        target, _, target_images, _ = _seed_consultation(db, account_id, storage=storage)
        other, _, other_images, _ = _seed_consultation(db, account_id, storage=storage)
        other_keys = [image.storage_key for image in other_images]

        target.state = ConsultationState.deleted
        db.commit()

        reconcile_terminal_media(db, storage, now=T0)

        assert other.source_session_id is not None
        for key in other_keys:
            assert storage.exists(key) is True

    with session_factory() as db:
        for image in other_images:
            row = db.get(PhotoUploadImage, image.id)
            assert row is not None
            assert row.state == PhotoImageState.ready


def test_run_cleanup_purges_terminal_and_preserves_active(session_factory, storage) -> None:
    from app.photo_service import create_upload_session, upload_image

    with session_factory() as db:
        account_id = _account(db)
        consultation, session, images, _ = _seed_consultation(db, account_id, storage=storage)
        terminal_keys = [image.storage_key for image in images]
        consultation.state = ConsultationState.deleted
        db.commit()

        active_session = create_upload_session(db, account_id, now=T0)
        active_image = upload_image(
            db,
            storage,
            account_id,
            active_session.id,
            uuid.uuid4(),
            io.BytesIO(_jpeg_bytes()),
            now=T0,
        )
        active_key = db.get(PhotoUploadImage, active_image.id).storage_key

        report = run_cleanup(db, storage, now=T0 + timedelta(hours=1))

        assert report.terminal_sessions_completed == 1
        assert report.terminal_objects_deleted == 2

    with session_factory() as db:
        for key in terminal_keys:
            assert storage.exists(key) is False
        assert storage.exists(active_key) is True
        assert db.get(PhotoUploadSession, session.id) is None
        assert db.get(PhotoUploadSession, active_session.id).state == PhotoUploadSessionState.active


def test_run_cleanup_busy_when_lock_unavailable(session_factory, storage) -> None:
    class BusyLock:
        def acquire(self) -> bool:
            return False

        def release(self) -> None:
            return None

    with session_factory() as db:
        report = run_cleanup(db, storage, now=T0, lock=BusyLock())

    assert report.busy is True
    assert report.deleted_files == 0
    assert report.terminal_sessions_discovered == 0


def test_run_cleanup_reports_filesystem_anomalies(session_factory, storage) -> None:
    shard = storage.normalized_dir / "ab"
    shard.mkdir(parents=True, exist_ok=True)
    (shard / "unexpected.txt").write_bytes(b"x")

    with session_factory() as db:
        report = run_cleanup(db, storage, now=T0)

    assert report.anomalies >= 1


# --- Open-state and media constraints --------------------------------------------------------


def test_open_consultation_requires_complete_fields(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        session = PhotoUploadSession(
            account_id=account_id,
            state=PhotoUploadSessionState.consumed,
            lease_expires_at=T0,
        )
        db.add(session)
        db.flush()

        with pytest.raises(IntegrityError):
            db.add(
                Consultation(
                    owner_id=account_id,
                    question=None,
                    context=None,
                    audience="public",
                    state=ConsultationState.open,
                    published_at=T0,
                    source_session_id=session.id,
                    fingerprint="x",
                )
            )
            db.commit()
        db.rollback()


def test_terminal_consultation_allows_detached_content(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, session, _, _ = _seed_consultation(db, account_id)
        consultation.state = ConsultationState.deleted
        consultation.question = None
        consultation.audience = None
        consultation.fingerprint = None
        consultation.source_session_id = None
        db.commit()

        row = db.get(Consultation, consultation.id)
        assert row.question is None
        assert row.audience is None


def test_sanitize_terminal_content_nulls_disallowed_fields(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account_id, audience="private")
        consultation.state = ConsultationState.deleted
        sanitize_terminal_content(consultation)
        db.commit()

        row = db.get(Consultation, consultation.id)
        assert row.question is None
        assert row.context is None
        assert row.audience is None
        assert row.fingerprint is None
        assert int(row.private_link_generation) == 0
        assert row.private_link_active is False
        assert row.owner_id == account_id
        assert row.state == ConsultationState.deleted


def test_photo_media_check_requires_detach_marker(session_factory) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(db, account_id)
        photo = db.scalar(
            select(ConsultationPhoto).where(ConsultationPhoto.consultation_id == consultation.id)
        )
        assert photo is not None

        photo.image_id = None
        photo.media_deleted_at = None
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


# --- Reconciliation validation: invalid terminal source sessions are anomalies, never processed ---


def _seed_terminal_with_foreign_session(session_factory, storage):
    with session_factory() as db:
        owner_id = _account(db)
        other_id = _account(db)
        session = PhotoUploadSession(
            account_id=other_id,
            state=PhotoUploadSessionState.consumed,
            lease_expires_at=T0,
        )
        db.add(session)
        db.flush()
        key = uuid.uuid4().hex
        storage.write_normalized(key, b"x")
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=key,
            width=10,
            height=10,
        )
        db.add(image)
        db.flush()
        consultation = Consultation(
            owner_id=owner_id,
            question="Q",
            context=None,
            audience="public",
            state=ConsultationState.deleted,
            published_at=T0,
            source_session_id=session.id,
            fingerprint=uuid.uuid4().hex[:32],
        )
        db.add(consultation)
        db.commit()
        return consultation.id, session.id, image.id, key


def test_reconcile_skips_foreign_owner_session(session_factory, storage) -> None:
    cid, sid, image_id, key = _seed_terminal_with_foreign_session(session_factory, storage)

    with session_factory() as db:
        report = reconcile_terminal_media(db, storage, now=T0)

    assert report.sessions_discovered == 1
    assert report.anomalies == 1
    assert report.objects_requested == 0
    assert report.sessions_completed == 0

    with session_factory() as db:
        assert storage.exists(key) is True
        row = db.get(PhotoUploadImage, image_id)
        assert row is not None and row.state == PhotoImageState.ready
        assert db.get(PhotoUploadSession, sid) is not None
        assert db.get(Consultation, cid).source_session_id == sid


def test_reconcile_skips_non_consumed_session(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        session = PhotoUploadSession(
            account_id=account_id,
            state=PhotoUploadSessionState.active,
            lease_expires_at=T0,
        )
        db.add(session)
        db.flush()
        key = uuid.uuid4().hex
        storage.write_normalized(key, b"x")
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=key,
            width=10,
            height=10,
        )
        db.add(image)
        db.flush()
        consultation = Consultation(
            owner_id=account_id,
            question="Q",
            context=None,
            audience="public",
            state=ConsultationState.deleted,
            published_at=T0,
            source_session_id=session.id,
            fingerprint=uuid.uuid4().hex[:32],
        )
        db.add(consultation)
        db.commit()
        cid, sid, image_id = consultation.id, session.id, image.id

    with session_factory() as db:
        report = reconcile_terminal_media(db, storage, now=T0)

    assert report.anomalies == 1
    assert report.objects_requested == 0
    assert report.sessions_completed == 0

    with session_factory() as db:
        assert storage.exists(key) is True
        row = db.get(PhotoUploadImage, image_id)
        assert row is not None and row.state == PhotoImageState.ready
        assert db.get(PhotoUploadSession, sid).state == PhotoUploadSessionState.active
        assert db.get(Consultation, cid).source_session_id == sid


def test_reconcile_skips_missing_session(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account(db)
        missing_id = uuid.uuid4()
        consultation = Consultation(
            owner_id=account_id,
            question="Q",
            context=None,
            audience="public",
            state=ConsultationState.deleted,
            published_at=T0,
            source_session_id=missing_id,
            fingerprint=uuid.uuid4().hex[:32],
        )
        db.add(consultation)
        db.commit()
        cid = consultation.id

    with session_factory() as db:
        report = reconcile_terminal_media(db, storage, now=T0)

    assert report.sessions_discovered == 1
    assert report.anomalies == 1
    assert report.objects_requested == 0

    with session_factory() as db:
        assert db.get(Consultation, cid).source_session_id == missing_id


def test_run_cleanup_counts_database_anomalies(session_factory, storage) -> None:
    _seed_terminal_with_foreign_session(session_factory, storage)

    with session_factory() as db:
        report = run_cleanup(db, storage, now=T0)

    assert report.anomalies >= 1
    assert report.terminal_sessions_discovered >= 1
    assert report.terminal_objects_requested == 0


# --- Verification failure after delete retains retry metadata ----------------------------------


def test_reconcile_persists_retry_metadata_on_verify_failure(
    session_factory, storage, monkeypatch
) -> None:
    with session_factory() as db:
        account_id = _account(db)
        consultation, _, images, _ = _seed_consultation(
            db, account_id, storage=storage, image_count=1
        )
        image_id = images[0].id
        key = images[0].storage_key
        cid = consultation.id

        consultation.state = ConsultationState.deleted
        db.commit()

        calls = {"n": 0}
        original_exists = storage.exists

        def flaky_exists(storage_key: str) -> bool:
            calls["n"] += 1
            if calls["n"] == 2:
                raise StorageError("verification failed")
            return original_exists(storage_key)

        monkeypatch.setattr(storage, "exists", flaky_exists)

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.objects_failed == 1
        assert report.sessions_completed == 0

    with session_factory() as db:
        row = db.get(PhotoUploadImage, image_id)
        assert row is not None
        assert row.state == PhotoImageState.revoked
        assert row.deletion_attempts == 1
        assert row.last_deletion_error == "storage failure"
        assert storage.exists(key) is False
        assert db.get(Consultation, cid).source_session_id is not None

    monkeypatch.undo()
    with session_factory() as db:
        second = reconcile_terminal_media(db, storage, now=T0 + timedelta(hours=1))
        assert second.sessions_completed == 1

    with session_factory() as db:
        assert db.get(PhotoUploadImage, image_id) is None
        assert db.get(Consultation, cid).source_session_id is None


# --- Structured logging and restricted status ---------------------------------------------------


def test_run_cleanup_logs_structured_summary_and_error_signals(
    session_factory, storage, caplog
) -> None:
    shard = storage.normalized_dir / "ab"
    shard.mkdir(parents=True, exist_ok=True)
    (shard / "unexpected.txt").write_bytes(b"x")

    with session_factory() as db:
        with caplog.at_level(logging.INFO):
            report = run_cleanup(db, storage, now=T0)

    assert report.anomalies >= 1
    assert any("photo maintenance summary" in record.message for record in caplog.records)
    assert any(
        "anomalies require restricted operator handling" in record.message
        for record in caplog.records
    )


def test_exit_code_reflects_anomalies_and_overdue() -> None:
    from app.cleanup import CleanupReport

    def report(**kwargs) -> CleanupReport:
        defaults = dict(
            abandoned_sessions=0,
            revoked_images=0,
            deleted_files=0,
            stale_attempts_removed=0,
            orphan_files_removed=0,
            tmp_files_removed=0,
            pending_beyond_alert=0,
        )
        defaults.update(kwargs)
        return CleanupReport(**defaults)

    assert _exit_code(report()) == 0
    assert _exit_code(report(busy=True)) == 2
    assert _exit_code(report(anomalies=1)) == 1
    assert _exit_code(report(pending_beyond_alert=1)) == 1
