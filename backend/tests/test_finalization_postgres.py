import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.consultation_deletion_service import delete_consultation
from app.consultation_finalization_service import (
    FinalizationDeclaration,
    finalize_consultation,
)
from app.consultation_removal_service import remove_consultation
from app.consultation_service import ConsultationConflictError, ConsultationUnavailableError
from app.db import Base
from app.models import (
    Account,
    Consultation,
    ConsultationFinalization,
    ConsultationOutcome,
    ConsultationPhoto,
    ConsultationRemoval,
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


def _consultation(
    db: Session, owner_id: uuid.UUID, *, count: int = 2
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    session = PhotoUploadSession(
        account_id=owner_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
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
    photos: list[uuid.UUID] = []
    for ordinal in range(count):
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
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo.id)
    db.commit()
    return consultation.id, photos


def _vote(db: Session, cid: uuid.UUID, voter_id: uuid.UUID, photo_id: uuid.UUID) -> None:
    db.add(Vote(consultation_id=cid, voter_id=voter_id, consultation_photo_id=photo_id))
    db.commit()


def _finalize(
    db: Session,
    cid: uuid.UUID,
    owner_id: uuid.UUID,
    operation_id: uuid.UUID,
    photo_ids: list[uuid.UUID],
) -> str:
    try:
        result = finalize_consultation(
            db,
            cid,
            owner_id,
            operation_id,
            FinalizationDeclaration(kind="selected", option_ids=tuple(photo_ids)),
        )
        return result.classification
    except ConsultationConflictError:
        return "conflict"
    except ConsultationUnavailableError:
        return "unavailable"


def _delete_open(db: Session, cid: uuid.UUID, owner_id: uuid.UUID) -> str:
    try:
        return delete_consultation(db, cid, owner_id, "open").classification
    except ConsultationConflictError:
        return "conflict"
    except ConsultationUnavailableError:
        return "unavailable"


def _remove(
    db: Session,
    cid: uuid.UUID,
    operation_id: uuid.UUID | None = None,
    reason: str = "other",
) -> str:
    try:
        return remove_consultation(
            db,
            consultation_id=cid,
            operation_id=operation_id or uuid.uuid4(),
            expected_state="open",
            operator_id="postgres.test",
            reason_code=reason,
        ).classification
    except ConsultationConflictError:
        return "conflict"
    except ConsultationUnavailableError:
        return "unavailable"


def test_vote_before_finalize_is_included(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photo_ids = _consultation(db, owner_id)
        _vote(db, cid, voter_id, photo_ids[0])

    with pg_factory() as db:
        result = finalize_consultation(
            db,
            cid,
            owner_id,
            uuid.uuid4(),
            FinalizationDeclaration(kind="selected", option_ids=(photo_ids[0],)),
        )

    assert result.summary.total_votes == 1
    assert result.matched == 1
    assert result.not_matched == 0

    with pg_factory() as db:
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None
        outcome = db.scalar(
            select(ConsultationOutcome).where(ConsultationOutcome.consultation_id == cid)
        )
        assert outcome is not None
        assert outcome.outcome.value == "matched"


def test_finalize_before_vote_denies_vote(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photo_ids = _consultation(db, owner_id)
        finalize_consultation(
            db,
            cid,
            owner_id,
            uuid.uuid4(),
            FinalizationDeclaration(kind="selected", option_ids=(photo_ids[0],)),
        )

    with pg_factory() as db:
        with pytest.raises(ConsultationUnavailableError):
            submit_vote(db, cid, voter_id, None, photo_ids[1])


def test_two_different_finalizers_only_first_commits(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, photo_ids = _consultation(db, owner_id)

    def run(payload: tuple[uuid.UUID, list[uuid.UUID]]) -> str:
        operation_id, ids = payload
        with pg_factory() as db:
            return _finalize(db, cid, owner_id, operation_id, ids)

    payloads = [(uuid.uuid4(), [photo_ids[0]]), (uuid.uuid4(), [photo_ids[1]])]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, payloads))

    assert outcomes.count("first") == 1
    assert outcomes.count("conflict") == 1

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        header = db.get(ConsultationFinalization, cid)
        assert header is not None


def test_concurrent_identical_retries_yield_one_commit(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, photo_ids = _consultation(db, owner_id)

    operation_id = uuid.uuid4()

    def run(_index: int) -> str:
        with pg_factory() as db:
            return _finalize(db, cid, owner_id, operation_id, [photo_ids[0]])

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(run, range(4)))

    assert outcomes.count("first") == 1
    assert outcomes.count("replay") == 3
    assert "conflict" not in outcomes
    assert "unavailable" not in outcomes


def test_delete_versus_finalize_race(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, photo_ids = _consultation(db, owner_id)

    def finalize_fn(_index: int) -> str:
        with pg_factory() as db:
            return _finalize(db, cid, owner_id, uuid.uuid4(), [photo_ids[0]])

    def delete_fn(_index: int) -> str:
        with pg_factory() as db:
            return _delete_open(db, cid, owner_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda fn: fn(0), [finalize_fn, delete_fn]))

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        state = row.state.value
        marker = row.author_deleted_at

    if "first" in outcomes:
        assert state == "finalized"
        assert marker is None
        assert "conflict" in outcomes
        assert db is not None
    else:
        assert state == "deleted"
        assert marker is not None
        assert "conflict" in outcomes


def test_removal_versus_finalize_race(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, photo_ids = _consultation(db, owner_id)

    def finalize_fn(_index: int) -> str:
        with pg_factory() as db:
            return _finalize(db, cid, owner_id, uuid.uuid4(), [photo_ids[0]])

    def remove_fn(_index: int) -> str:
        with pg_factory() as db:
            return _remove(db, cid)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda fn: fn(0), [finalize_fn, remove_fn]))

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        state = row.state.value

    if "first" in outcomes:
        assert state == "finalized"
        assert "conflict" in outcomes
    else:
        assert state == "removed"
        assert "unavailable" in outcomes


def test_concurrent_identical_removals_yield_first_and_replay(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)
    operation_id = uuid.uuid4()

    def remove_fn(_index: int) -> str:
        with pg_factory() as db:
            return _remove(db, cid, operation_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(remove_fn, range(2)))

    assert sorted(outcomes) == ["first", "replay"]
    with pg_factory() as db:
        assert db.get(Consultation, cid).state == ConsultationState.removed
        assert db.get(ConsultationRemoval, cid).operation_id == operation_id


def test_concurrent_different_removals_yield_first_and_conflict(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)
    operations = [uuid.uuid4(), uuid.uuid4()]

    def remove_fn(operation_id: uuid.UUID) -> str:
        with pg_factory() as db:
            return _remove(db, cid, operation_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(remove_fn, operations))

    assert sorted(outcomes) == ["conflict", "first"]
    with pg_factory() as db:
        audit = db.get(ConsultationRemoval, cid)
        assert audit is not None
        assert audit.operation_id in operations


def test_concurrent_cross_target_operation_reuse_is_a_conflict(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        first_id, _ = _consultation(db, owner_id)
        second_id, _ = _consultation(db, owner_id)
    operation_id = uuid.uuid4()

    def remove_fn(cid: uuid.UUID) -> tuple[uuid.UUID, str]:
        with pg_factory() as db:
            return cid, _remove(db, cid, operation_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = dict(pool.map(remove_fn, [first_id, second_id]))

    assert sorted(outcomes.values()) == ["conflict", "first"]
    with pg_factory() as db:
        audits = list(
            db.scalars(
                select(ConsultationRemoval).where(ConsultationRemoval.operation_id == operation_id)
            ).all()
        )
        assert len(audits) == 1
        winner = audits[0].consultation_id
        loser = second_id if winner == first_id else first_id
        assert db.get(Consultation, winner).state == ConsultationState.removed
        assert db.get(Consultation, loser).state == ConsultationState.open


def test_removal_versus_author_deletion_race(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        cid, _ = _consultation(db, owner_id)

    def removal_fn(_index: int) -> tuple[str, str]:
        with pg_factory() as db:
            return "removal", _remove(db, cid)

    def deletion_fn(_index: int) -> tuple[str, str]:
        with pg_factory() as db:
            return "deletion", _delete_open(db, cid, owner_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = dict(pool.map(lambda fn: fn(0), [removal_fn, deletion_fn]))

    with pg_factory() as db:
        row = db.get(Consultation, cid)
        audit = db.get(ConsultationRemoval, cid)
        if row.state == ConsultationState.removed:
            assert outcomes == {"removal": "first", "deletion": "unavailable"}
            assert audit is not None
            assert row.author_deleted_at is None
        else:
            assert row.state == ConsultationState.deleted
            assert outcomes == {"removal": "conflict", "deletion": "first"}
            assert audit is None
            assert row.author_deleted_at is not None


def test_removal_serializes_with_vote_and_leaves_no_raw_vote(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photo_ids = _consultation(db, owner_id)

    def removal_fn(_index: int) -> str:
        with pg_factory() as db:
            return _remove(db, cid)

    def vote_fn(_index: int) -> str:
        with pg_factory() as db:
            try:
                submit_vote(db, cid, voter_id, None, photo_ids[0])
                return "submitted"
            except ConsultationUnavailableError:
                return "unavailable"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda fn: fn(0), [removal_fn, vote_fn]))

    assert outcomes[0] == "first"
    assert outcomes[1] in {"submitted", "unavailable"}
    with pg_factory() as db:
        assert db.get(Consultation, cid).state == ConsultationState.removed
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None
