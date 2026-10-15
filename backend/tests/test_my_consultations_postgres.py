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
    ConsultationState,
    PhotoUploadSession,
    PhotoUploadSessionState,
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")


@pytest.fixture()
def pg_factory() -> sessionmaker[Session]:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, pool_size=20, max_overflow=0)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


def _account_id(db: Session) -> uuid.UUID:
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


def _insert_consultation(
    db: Session, account_id: uuid.UUID, published_at: datetime, question: str = "Q"
) -> Consultation:
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.active,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
    db.flush()
    consultation = Consultation(
        owner_id=account_id,
        question=question,
        context=None,
        audience="public",
        state=ConsultationState.open,
        published_at=published_at,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
    )
    db.add(consultation)
    db.commit()
    return consultation


def test_uuid_tie_ordering_matches_native_postgres_order(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account_id(db)
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        consultations = [
            _insert_consultation(db, account_id, published_at, question=f"Q{i}") for i in range(5)
        ]

        result = consultation_service.list_my_consultations(db, account_id, "open", 50, None)

        expected = sorted((str(c.id) for c in consultations), reverse=True)
        assert [item.id for item in result.items] == expected


def test_cursor_pagination_with_ties_is_stable_on_postgres(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account_id(db)
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        consultations = [
            _insert_consultation(db, account_id, published_at, question=f"Q{i}") for i in range(25)
        ]
        expected = sorted((str(c.id) for c in consultations), reverse=True)

        collected: list[str] = []
        cursor = None
        while True:
            result = consultation_service.list_my_consultations(db, account_id, "open", 20, cursor)
            collected.extend(item.id for item in result.items)
            if result.next_cursor is None:
                break
            decoded = consultation_service.decode_cursor(result.next_cursor)
            assert decoded is not None
            cursor = (decoded[1], decoded[2])

        assert collected == expected
        assert len(collected) == len(set(collected)) == 25


def test_cross_account_cursor_reuse_exposes_nothing(pg_factory) -> None:
    with pg_factory() as db:
        owner_a = _account_id(db)
        owner_b = _account_id(db)
        for i in range(3):
            _insert_consultation(db, owner_a, datetime(2026, 1, 1, 12, i), question=f"A{i}")

        first = consultation_service.list_my_consultations(db, owner_a, "open", 1, None)
        assert first.next_cursor is not None
        decoded = consultation_service.decode_cursor(first.next_cursor)
        assert decoded is not None
        cursor = (decoded[1], decoded[2])

        other = consultation_service.list_my_consultations(db, owner_b, "open", 50, cursor)
        assert other.items == []
        assert other.next_cursor is None


def test_timestamp_and_uuid_descending_order(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account_id(db)
        newer = _insert_consultation(
            db, account_id, datetime(2026, 1, 2, 0, 0, 0), question="newer"
        )
        older = _insert_consultation(
            db, account_id, datetime(2026, 1, 1, 0, 0, 0), question="older"
        )

        result = consultation_service.list_my_consultations(db, account_id, "open", 50, None)
        assert [item.id for item in result.items] == [str(newer.id), str(older.id)]
