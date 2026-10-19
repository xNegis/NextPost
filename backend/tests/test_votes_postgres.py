import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

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
from app.vote_service import (
    ConsultationUnavailableError,
    VoteAlreadyRecordedError,
    submit_vote,
)

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
        state=PhotoUploadSessionState.active,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
    db.flush()
    image_a = PhotoUploadImage(
        upload_session_id=session.id,
        attempt_id=uuid.uuid4(),
        state="ready",
        storage_key=f"k{uuid.uuid4().hex[:12]}",
        width=64,
        height=64,
    )
    image_b = PhotoUploadImage(
        upload_session_id=session.id,
        attempt_id=uuid.uuid4(),
        state="ready",
        storage_key=f"k{uuid.uuid4().hex[:12]}",
        width=64,
        height=64,
    )
    db.add_all([image_a, image_b])
    db.flush()
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
    photo_a = ConsultationPhoto(consultation_id=consultation.id, image_id=image_a.id, ordinal=0)
    photo_b = ConsultationPhoto(consultation_id=consultation.id, image_id=image_b.id, ordinal=1)
    db.add_all([photo_a, photo_b])
    db.commit()
    return consultation.id, [photo_a.id, photo_b.id]


def _seed(pg_factory) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        consultation_id, photo_ids = _consultation(db, owner_id)
        return owner_id, voter_id, consultation_id, photo_ids


def test_same_account_same_option_duplicate_clicks_yield_one_vote(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)
    chosen = photo_ids[0]

    def submit(_index: int) -> str:
        with pg_factory() as db:
            result = submit_vote(db, consultation_id, voter_id, None, chosen)
            return "created" if result.created else "replay"

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(submit, range(4)))

    assert outcomes.count("created") == 1
    assert outcomes.count("replay") == 3

    with pg_factory() as db:
        votes = (
            db.execute(
                select(Vote).where(
                    Vote.consultation_id == consultation_id, Vote.voter_id == voter_id
                )
            )
            .scalars()
            .all()
        )
    assert len(votes) == 1
    assert votes[0].consultation_photo_id == chosen


def test_same_account_different_options_one_wins_other_conflicts(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)

    def submit(photo_id: uuid.UUID) -> str:
        with pg_factory() as db:
            try:
                submit_vote(db, consultation_id, voter_id, None, photo_id)
                return "ok"
            except VoteAlreadyRecordedError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, [photo_ids[0], photo_ids[1]]))

    assert sorted(outcomes) == ["conflict", "ok"]

    with pg_factory() as db:
        votes = (
            db.execute(
                select(Vote).where(
                    Vote.consultation_id == consultation_id, Vote.voter_id == voter_id
                )
            )
            .scalars()
            .all()
        )
    assert len(votes) == 1


def test_many_accounts_vote_for_distinct_options(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)

    extra_voters = []
    with pg_factory() as db:
        for index in range(5):
            extra_voters.append(_account(db, f"v{index}@example.com", f"V{index}"))

    def submit(args) -> str:
        voter, photo = args
        with pg_factory() as db:
            submit_vote(db, consultation_id, voter, None, photo)
            return "ok"

    pairs = [(voter_id, photo_ids[0])] + [
        (v, photo_ids[index % 2]) for index, v in enumerate(extra_voters)
    ]
    with ThreadPoolExecutor(max_workers=len(pairs)) as pool:
        outcomes = list(pool.map(submit, pairs))

    assert outcomes == ["ok"] * len(pairs)

    with pg_factory() as db:
        count = (
            db.execute(select(Vote).where(Vote.consultation_id == consultation_id)).scalars().all()
        )
    assert len(count) == len(pairs)


def test_delayed_retry_after_commit_recovers_existing_vote(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)
    chosen = photo_ids[0]

    with pg_factory() as db:
        first = submit_vote(db, consultation_id, voter_id, None, chosen)
    assert first.created is True

    with pg_factory() as db:
        replay = submit_vote(db, consultation_id, voter_id, None, chosen)
    assert replay.created is False
    assert replay.photo_id == str(chosen)


def test_vote_versus_terminal_writer_shared_lock(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)
    chosen = photo_ids[0]

    def terminalize() -> str:
        with pg_factory() as db:
            row = db.execute(
                select(Consultation).where(Consultation.id == consultation_id).with_for_update()
            ).scalar_one()
            row.state = ConsultationState.finalized
            db.commit()
            return "finalized"

    def vote() -> str:
        with pg_factory() as db:
            try:
                submit_vote(db, consultation_id, voter_id, None, chosen)
                return "voted"
            except ConsultationUnavailableError:
                return "denied"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda fn: fn(), [terminalize, vote]))

    assert sorted(outcomes) == ["denied", "finalized"]

    with pg_factory() as db:
        votes = (
            db.execute(select(Vote).where(Vote.consultation_id == consultation_id)).scalars().all()
        )
    assert votes == []


def test_vote_before_terminal_commit_is_durable(pg_factory) -> None:
    _, voter_id, consultation_id, photo_ids = _seed(pg_factory)
    chosen = photo_ids[0]

    with pg_factory() as db:
        submit_vote(db, consultation_id, voter_id, None, chosen)

    with pg_factory() as db:
        row = db.execute(
            select(Consultation).where(Consultation.id == consultation_id).with_for_update()
        ).scalar_one()
        row.state = ConsultationState.deleted
        db.commit()

    with pg_factory() as db:
        votes = (
            db.execute(
                select(Vote).where(
                    Vote.consultation_id == consultation_id, Vote.voter_id == voter_id
                )
            )
            .scalars()
            .all()
        )
    assert len(votes) == 1
