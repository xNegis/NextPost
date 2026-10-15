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
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")


@pytest.fixture()
def pg_factory() -> sessionmaker[Session]:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, pool_size=20, max_overflow=0)
    # The feed is global across authors, so each test starts from a clean schema to
    # avoid cross-test contamination from prior inserts.
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


def _insert_public_consultation(
    db: Session,
    account_id: uuid.UUID,
    published_at: datetime,
    question: str = "Q",
    *,
    audience: str = "public",
) -> Consultation:
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.active,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
    db.flush()
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
    consultation = Consultation(
        owner_id=account_id,
        question=question,
        context=None,
        audience=audience,
        state=ConsultationState.open,
        published_at=published_at,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
        private_link_generation=1 if audience == "private" else 0,
        private_link_active=audience == "private",
    )
    db.add(consultation)
    db.flush()
    db.add(ConsultationPhoto(consultation_id=consultation.id, image_id=image.id, ordinal=0))
    db.commit()
    return consultation


def test_feed_uuid_tie_ordering_matches_native_postgres_order(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account(db, "a@example.com", "A")
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        consultations = [
            _insert_public_consultation(db, account_id, published_at, question=f"Q{i}")
            for i in range(5)
        ]

        result = consultation_service.list_feed(db, account_id, 50, None)

        expected = sorted((str(c.id) for c in consultations), reverse=True)
        assert [item.id for item in result.items] == expected


def test_feed_cursor_pagination_with_ties_is_stable_on_postgres(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account(db, "a@example.com", "A")
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        consultations = [
            _insert_public_consultation(db, account_id, published_at, question=f"Q{i}")
            for i in range(25)
        ]
        expected = sorted((str(c.id) for c in consultations), reverse=True)

        collected: list[str] = []
        cursor = None
        while True:
            result = consultation_service.list_feed(db, account_id, 20, cursor)
            collected.extend(item.id for item in result.items)
            if result.next_cursor is None:
                break
            decoded = consultation_service.decode_feed_cursor(result.next_cursor)
            assert decoded is not None
            cursor = (decoded[0], decoded[1])

        assert collected == expected
        assert len(collected) == len(set(collected)) == 25


def test_feed_timestamp_and_uuid_descending_order(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account(db, "a@example.com", "A")
        newer = _insert_public_consultation(
            db, account_id, datetime(2026, 1, 2, 0, 0, 0), question="newer"
        )
        older = _insert_public_consultation(
            db, account_id, datetime(2026, 1, 1, 0, 0, 0), question="older"
        )

        result = consultation_service.list_feed(db, account_id, 50, None)
        assert [item.id for item in result.items] == [str(newer.id), str(older.id)]


def test_feed_excludes_private_and_includes_public_across_authors(pg_factory) -> None:
    with pg_factory() as db:
        owner_a = _account(db, "a@example.com", "A")
        owner_b = _account(db, "b@example.com", "B")
        _insert_public_consultation(db, owner_a, datetime(2026, 1, 1, 12, 0, 0), audience="private")
        pub = _insert_public_consultation(db, owner_b, datetime(2026, 1, 1, 12, 0, 0))

        result = consultation_service.list_feed(db, owner_a, 50, None)
        assert [item.id for item in result.items] == [str(pub.id)]
        assert result.items[0].is_owner is False
        assert result.items[0].owner_nickname.startswith("B")


def test_feed_insertion_between_pages_appears_on_refresh(pg_factory) -> None:
    with pg_factory() as db:
        account_id = _account(db, "a@example.com", "A")
        for i in range(3):
            _insert_public_consultation(
                db, account_id, datetime(2026, 1, 1, 12, 0, 0), question=f"O{i}"
            )
        first = consultation_service.list_feed(db, account_id, 2, None)
        assert len(first.items) == 2
        assert first.next_cursor is not None

        newest = _insert_public_consultation(
            db, account_id, datetime(2026, 1, 2, 12, 0, 0), question="newest"
        )
        refreshed = consultation_service.list_feed(db, account_id, 50, None)
        assert refreshed.items[0].id == str(newest.id)
        assert len(refreshed.items) == 4
        assert refreshed.items[0].question == "newest"
