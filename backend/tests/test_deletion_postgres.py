import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.consultation_deletion_service import delete_consultation
from app.consultation_service import ConsultationConflictError, ConsultationUnavailableError
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


def _consultation(db: Session, owner_id: uuid.UUID) -> tuple[uuid.UUID, list[uuid.UUID]]:
    session = PhotoUploadSession(
        account_id=owner_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
    db.flush()
    images = []
    for _ in range(2):
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state="ready",
            storage_key=f"k{uuid.uuid4().hex[:12]}",
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
    photos = []
    for ordinal, image in enumerate(images):
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo)
    db.commit()
    return consultation.id, [photo.id for photo in photos]


def _finalize(db: Session, cid: uuid.UUID) -> str:
    row = db.execute(
        select(Consultation).where(Consultation.id == cid).with_for_update()
    ).scalar_one_or_none()
    if row is None or row.state != ConsultationState.open:
        return "lost"
    row.state = ConsultationState.finalized
    db.commit()
    return "finalized"


def _delete_open(db: Session, cid: uuid.UUID, owner_id: uuid.UUID) -> str:
    try:
        outcome = delete_consultation(db, cid, owner_id, "open")
        return outcome.classification
    except ConsultationConflictError:
        return "conflict"
    except ConsultationUnavailableError:
        return "unavailable"


def test_vote_before_delete_is_removed(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photo_ids = _consultation(db, owner_id)
        submit_vote(db, cid, voter_id, None, photo_ids[0])

    with pg_factory() as db:
        outcome = delete_consultation(db, cid, owner_id, "open")

    assert outcome.votes_removed == 1

    with pg_factory() as db:
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.deleted
        assert row.author_deleted_at is not None


def test_delete_before_vote_denies_vote(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photo_ids = _consultation(db, owner_id)
        delete_consultation(db, cid, owner_id, "open")

    with pg_factory() as db:
        with pytest.raises(ConsultationUnavailableError):
            submit_vote(db, cid, voter_id, None, photo_ids[0])


def test_delete_versus_finalize_race(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)

    def delete_fn(_index: int) -> str:
        with pg_factory() as db:
            return _delete_open(db, cid, owner_id)

    def finalize_fn(_index: int) -> str:
        with pg_factory() as db:
            return _finalize(db, cid)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda fn: fn(0), [delete_fn, finalize_fn]))

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        state = row.state.value
        marker = row.author_deleted_at

    if "first" in outcomes:
        assert state == "deleted"
        assert marker is not None
        assert "lost" in outcomes
    else:
        assert "finalized" in outcomes
        assert state == "finalized"
        assert marker is None
        assert "conflict" in outcomes


def test_finalize_then_stale_open_delete_conflicts_then_finalized_delete_withdraws(
    pg_factory,
) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)

    with pg_factory() as db:
        assert _finalize(db, cid) == "finalized"

    with pg_factory() as db:
        with pytest.raises(ConsultationConflictError):
            delete_consultation(db, cid, owner_id, "open")
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        assert row.author_deleted_at is None

    with pg_factory() as db:
        outcome = delete_consultation(db, cid, owner_id, "finalized")
        assert outcome.classification == "first"

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        assert row.author_deleted_at is not None


def test_concurrent_identical_deletes_yield_one_commit(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)

    def run(_index: int) -> str:
        with pg_factory() as db:
            return _delete_open(db, cid, owner_id)

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(run, range(4)))

    assert outcomes.count("first") == 1
    assert outcomes.count("replay") == 3
    assert "conflict" not in outcomes
    assert "unavailable" not in outcomes

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.deleted
        assert row.author_deleted_at is not None
