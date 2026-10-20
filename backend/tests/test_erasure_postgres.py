import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.cleanup import PostgresAdvisoryMaintenanceLock, run_cleanup
from app.consultation_service import (
    ConsultationUnavailableError,
    read_consultation_detail,
)
from app.db import Base
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
    Vote,
)
from app.photo_erasure_service import mark_media_for_erasure
from app.storage import PhotoStorage
from app.vote_service import submit_vote

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")


@pytest.fixture()
def pg_factory() -> sessionmaker[Session]:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, pool_size=20, max_overflow=0)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


def _account(db: Session, email: str, alias: str) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"{email.split('@')[0]}{suffix}@{email.split('@')[1]}",
        alias=f"{alias}{suffix}",
        alias_canonical=f"{alias}{suffix}".lower(),
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account.id


def _seed_published(pg_factory, storage: PhotoStorage):
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        session = PhotoUploadSession(
            account_id=owner_id,
            state=PhotoUploadSessionState.consumed,
            lease_expires_at=datetime(2030, 1, 1),
        )
        db.add(session)
        db.flush()
        images = []
        for _ in range(2):
            key = uuid.uuid4().hex
            storage.write_normalized(key, b"x")
            image = PhotoUploadImage(
                upload_session_id=session.id,
                attempt_id=uuid.uuid4(),
                state="ready",
                storage_key=key,
                width=64,
                height=64,
            )
            db.add(image)
            db.flush()
            images.append(image)
        consultation = Consultation(
            owner_id=owner_id,
            question="Q",
            context=None,
            audience="public",
            state=ConsultationState.open,
            published_at=datetime(2026, 1, 1, 12, 0, 0),
            source_session_id=session.id,
            fingerprint=uuid.uuid4().hex[:32],
        )
        db.add(consultation)
        db.flush()
        photos = [
            ConsultationPhoto(consultation_id=consultation.id, image_id=images[i].id, ordinal=i)
            for i in range(2)
        ]
        db.add_all(photos)
        db.commit()
        return (
            owner_id,
            voter_id,
            consultation.id,
            [photo.id for photo in photos],
            [image.storage_key for image in images],
        )


def _terminalize(db: Session, consultation_id: uuid.UUID) -> None:
    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one()
    mark_media_for_erasure(db, consultation)
    consultation.state = ConsultationState.deleted
    db.commit()


def test_advisory_leader_lock_excludes_second_leader() -> None:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)
    first = PostgresAdvisoryMaintenanceLock(engine)
    second = PostgresAdvisoryMaintenanceLock(engine)

    assert first.acquire() is True
    assert second.acquire() is False
    first.release()
    assert second.acquire() is True
    second.release()
    engine.dispose()


def test_run_cleanup_reports_busy_when_leader_held(pg_factory, tmp_path) -> None:
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL)

    leader = PostgresAdvisoryMaintenanceLock(engine)
    assert leader.acquire() is True
    contender = PostgresAdvisoryMaintenanceLock(engine)

    with pg_factory() as db:
        report = run_cleanup(db, storage, lock=contender)

    assert report.busy is True
    leader.release()
    engine.dispose()


def test_terminal_marker_revokes_access_and_cleanup_deletes(pg_factory, tmp_path) -> None:
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()
    owner_id, voter_id, consultation_id, photo_ids, keys = _seed_published(pg_factory, storage)

    with pg_factory() as db:
        _terminalize(db, consultation_id)

    with pg_factory() as db:
        with pytest.raises(ConsultationUnavailableError):
            submit_vote(db, consultation_id, voter_id, None, photo_ids[0])
        with pytest.raises(ConsultationUnavailableError):
            read_consultation_detail(db, storage, consultation_id, owner_id, None)

    for key in keys:
        assert storage.exists(key) is True

    with pg_factory() as db:
        report = run_cleanup(db, storage)

    assert report.terminal_sessions_completed == 1
    assert report.terminal_objects_deleted == 2
    for key in keys:
        assert storage.exists(key) is False


def test_vote_before_terminal_marker_is_preserved(pg_factory, tmp_path) -> None:
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()
    _, voter_id, consultation_id, photo_ids, _ = _seed_published(pg_factory, storage)

    with pg_factory() as db:
        submit_vote(db, consultation_id, voter_id, None, photo_ids[0])

    with pg_factory() as db:
        _terminalize(db, consultation_id)

    with pg_factory() as db:
        votes = (
            db.execute(select(Vote).where(Vote.consultation_id == consultation_id)).scalars().all()
        )
        assert len(votes) == 1
        assert votes[0].consultation_photo_id == photo_ids[0]


def test_terminal_marker_reconciles_legacy_ready_fixture(pg_factory, tmp_path) -> None:
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()
    _, _, consultation_id, _, keys = _seed_published(pg_factory, storage)

    # Simulate a pre-RF-37 terminal fixture: the consultation is terminal but its images were
    # never marked revoked by a marker (still ready).
    with pg_factory() as db:
        consultation = db.get(Consultation, consultation_id)
        consultation.state = ConsultationState.deleted
        db.commit()

    with pg_factory() as db:
        report = run_cleanup(db, storage)

    assert report.terminal_sessions_discovered == 1
    assert report.terminal_objects_deleted == 2
    assert report.terminal_sessions_completed == 1
    for key in keys:
        assert storage.exists(key) is False
