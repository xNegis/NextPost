import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import consultation_service
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
    db: Session, owner_id: uuid.UUID, *, count: int = 3
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    session = PhotoUploadSession(
        account_id=owner_id,
        state=PhotoUploadSessionState.active,
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
    photo_ids: list[uuid.UUID] = []
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
        photo_ids.append(photo.id)
    db.commit()
    return consultation.id, photo_ids


def _vote(
    db: Session, consultation_id: uuid.UUID, voter_id: uuid.UUID, photo_id: uuid.UUID
) -> None:
    db.add(Vote(consultation_id=consultation_id, voter_id=voter_id, consultation_photo_id=photo_id))
    db.commit()


def test_results_outer_join_preserves_zero_vote_options(pg_factory) -> None:
    with pg_factory() as db:
        owner = _account(db, "owner@example.com", "Owner")
        consultation_id, photo_ids = _consultation(db, owner)
        voter = _account(db, "voter@example.com", "Voter")
        _vote(db, consultation_id, voter, photo_ids[0])

        result = consultation_service.read_my_consultation_results(db, consultation_id, owner)

    assert result.total_votes == 1
    assert [option.ordinal for option in result.options] == [0, 1, 2]
    assert [option.vote_count for option in result.options] == [1, 0, 0]
    assert sum(option.vote_count for option in result.options) == result.total_votes


def test_results_ties_and_immutable_ordinal_order(pg_factory) -> None:
    with pg_factory() as db:
        owner = _account(db, "owner@example.com", "Owner")
        consultation_id, photo_ids = _consultation(db, owner)
        for index in range(4):
            voter = _account(db, f"v{index}@example.com", f"V{index}")
            _vote(db, consultation_id, voter, photo_ids[index % 2])

        result = consultation_service.read_my_consultation_results(db, consultation_id, owner)

    assert result.total_votes == 4
    assert [option.ordinal for option in result.options] == [0, 1, 2]
    assert [option.vote_count for option in result.options] == [2, 2, 0]


def test_results_require_ownership(pg_factory) -> None:
    with pg_factory() as db:
        owner = _account(db, "owner@example.com", "Owner")
        other = _account(db, "other@example.com", "Other")
        consultation_id, _ = _consultation(db, owner)

        with pytest.raises(consultation_service.ConsultationUnavailableError):
            consultation_service.read_my_consultation_results(db, consultation_id, other)


def test_results_reject_terminal_consultation(pg_factory) -> None:
    with pg_factory() as db:
        owner = _account(db, "owner@example.com", "Owner")
        consultation_id, _ = _consultation(db, owner)
        consultation = db.get(Consultation, consultation_id)
        consultation.state = ConsultationState.finalized
        db.commit()

        with pytest.raises(consultation_service.ConsultationUnavailableError):
            consultation_service.read_my_consultation_results(db, consultation_id, owner)


def test_list_totals_are_set_wise(pg_factory) -> None:
    with pg_factory() as db:
        owner = _account(db, "owner@example.com", "Owner")
        first_id, first_photos = _consultation(db, owner)
        second_id, second_photos = _consultation(db, owner)
        voter_a = _account(db, "a@example.com", "A")
        voter_b = _account(db, "b@example.com", "B")
        _vote(db, first_id, voter_a, first_photos[0])
        _vote(db, second_id, voter_a, second_photos[0])
        _vote(db, second_id, voter_b, second_photos[1])

        result = consultation_service.list_my_consultations(db, owner, "open", 50, None)

    totals = {item.id: item.total_votes for item in result.items}
    assert totals == {str(first_id): 1, str(second_id): 2}
