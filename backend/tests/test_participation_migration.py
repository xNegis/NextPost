import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from app.config import get_settings

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def _reset_schema(url: str) -> None:
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()


def _run(url: str, action: str, revision: str) -> None:
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    config = _config(url)
    getattr(command, action)(config, revision)
    get_settings.cache_clear()


def test_fresh_upgrade_creates_voter_created_index() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    index_names = {index["name"] for index in inspector.get_indexes("votes")}
    assert "ix_votes_voter_created" in index_names
    engine.dispose()


def test_upgrade_from_0008_preserves_votes_without_backfill() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20261020_0008")

    account_id = uuid.uuid4()
    session_id = uuid.uuid4()
    consultation_id = uuid.uuid4()
    voter_id = uuid.uuid4()
    photo_id = uuid.uuid4()
    image_id = uuid.uuid4()
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, email, alias, alias_canonical, password_hash) "
                "VALUES (:id, :email, :alias, :alias_canonical, :password_hash)"
            ),
            {
                "id": str(account_id),
                "email": "owner@example.com",
                "alias": "Owner",
                "alias_canonical": "owner",
                "password_hash": "x",
            },
        )
        conn.execute(
            text(
                "INSERT INTO accounts (id, email, alias, alias_canonical, password_hash) "
                "VALUES (:id, :email, :alias, :alias_canonical, :password_hash)"
            ),
            {
                "id": str(voter_id),
                "email": "voter@example.com",
                "alias": "Voter",
                "alias_canonical": "voter",
                "password_hash": "x",
            },
        )
        conn.execute(
            text(
                "INSERT INTO photo_upload_sessions (id, account_id, state, lease_expires_at) "
                "VALUES (:id, :account_id, 'consumed', :lease)"
            ),
            {"id": str(session_id), "account_id": str(account_id), "lease": datetime(2030, 1, 1)},
        )
        conn.execute(
            text(
                "INSERT INTO consultations (id, owner_id, question, context, audience, state, "
                "published_at, source_session_id, fingerprint, private_link_generation, "
                "private_link_active) VALUES (:id, :owner_id, :question, :context, :audience, "
                ":state, :published_at, :source_session_id, :fingerprint, 0, false)"
            ),
            {
                "id": str(consultation_id),
                "owner_id": str(account_id),
                "question": "Q",
                "context": None,
                "audience": "public",
                "state": "open",
                "published_at": datetime(2026, 1, 1, 12, 0, 0),
                "source_session_id": str(session_id),
                "fingerprint": uuid.uuid4().hex[:32],
            },
        )
        conn.execute(
            text(
                "INSERT INTO photo_upload_images (id, upload_session_id, attempt_id, state, "
                "storage_key, width, height) VALUES (:id, :session_id, :attempt_id, 'ready', "
                ":storage_key, 64, 64)"
            ),
            {
                "id": str(image_id),
                "session_id": str(session_id),
                "attempt_id": str(uuid.uuid4()),
                "storage_key": f"k{uuid.uuid4().hex[:12]}",
            },
        )
        conn.execute(
            text(
                "INSERT INTO consultation_photos (id, consultation_id, image_id, ordinal) "
                "VALUES (:id, :consultation_id, :image_id, 0)"
            ),
            {
                "id": str(photo_id),
                "consultation_id": str(consultation_id),
                "image_id": str(image_id),
            },
        )
        conn.execute(
            text(
                "INSERT INTO votes (id, consultation_id, voter_id, consultation_photo_id) "
                "VALUES (:id, :consultation_id, :voter_id, :photo_id)"
            ),
            {
                "id": str(uuid.uuid4()),
                "consultation_id": str(consultation_id),
                "voter_id": str(voter_id),
                "photo_id": str(photo_id),
            },
        )
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM votes WHERE voter_id = :voter_id"),
            {"voter_id": str(voter_id)},
        ).scalar_one()
        assert count == 1
    inspector = inspect(engine)
    assert "ix_votes_voter_created" in {index["name"] for index in inspector.get_indexes("votes")}
    engine.dispose()


def test_downgrade_drops_only_the_new_index() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _run(TEST_DATABASE_URL, "downgrade", "20261020_0008")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    assert "ix_votes_voter_created" not in {
        index["name"] for index in inspector.get_indexes("votes")
    }
    assert "votes" in inspector.get_table_names()
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")
