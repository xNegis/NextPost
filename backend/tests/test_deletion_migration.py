import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

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


def _raw_seed_consultation(url: str, *, state: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed one consultation via raw SQL compatible with revision 0006 (no marker column)."""
    suffix = uuid.uuid4().hex[:8]
    account_id = uuid.uuid4()
    session_id = uuid.uuid4()
    consultation_id = uuid.uuid4()
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, email, alias, alias_canonical, password_hash) "
                "VALUES (:id, :email, :alias, :alias_canonical, :password_hash)"
            ),
            {
                "id": str(account_id),
                "email": f"owner{suffix}@example.com",
                "alias": f"Owner{suffix}",
                "alias_canonical": f"owner{suffix}",
                "password_hash": "x",
            },
        )
        conn.execute(
            text(
                "INSERT INTO photo_upload_sessions (id, account_id, state, lease_expires_at) "
                "VALUES (:id, :account_id, 'consumed', :lease)"
            ),
            {
                "id": str(session_id),
                "account_id": str(account_id),
                "lease": datetime(2030, 1, 1),
            },
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
                "state": state,
                "published_at": datetime(2026, 1, 1, 12, 0, 0),
                "source_session_id": str(session_id),
                "fingerprint": uuid.uuid4().hex[:32],
            },
        )
    engine.dispose()
    return account_id, consultation_id


def test_fresh_upgrade_adds_author_deletion_schema() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)

    consultation_columns = {c["name"]: c for c in inspector.get_columns("consultations")}
    assert "author_deleted_at" in consultation_columns
    assert consultation_columns["author_deleted_at"]["nullable"] is True

    checks = {c["name"] for c in inspector.get_check_constraints("consultations")}
    assert "ck_consultations_author_deleted" in checks

    indexes = {i["name"] for i in inspector.get_indexes("consultations")}
    assert "ix_consultations_owner_state_author_deleted" in indexes
    engine.dispose()


def test_upgrade_from_0006_preserves_open_and_finalized_rows() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20261019_0006")

    _, open_id = _raw_seed_consultation(TEST_DATABASE_URL, state="open")
    _, finalized_id = _raw_seed_consultation(TEST_DATABASE_URL, state="finalized")

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        for cid in (open_id, finalized_id):
            marker = conn.execute(
                text("SELECT author_deleted_at FROM consultations WHERE id = :id"),
                {"id": str(cid)},
            ).scalar_one()
            assert marker is None
    engine.dispose()


def test_marker_requires_terminal_state() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, open_id = _raw_seed_consultation(TEST_DATABASE_URL, state="open")

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE consultations SET author_deleted_at = now() WHERE id = :id"),
                {"id": str(open_id)},
            )
    engine.dispose()


def test_marker_allowed_on_deleted_and_finalized() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, open_id = _raw_seed_consultation(TEST_DATABASE_URL, state="open")
    _, finalized_id = _raw_seed_consultation(TEST_DATABASE_URL, state="finalized")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE consultations SET state = 'deleted', author_deleted_at = now() "
                "WHERE id = :id"
            ),
            {"id": str(open_id)},
        )
        conn.execute(
            text("UPDATE consultations SET author_deleted_at = now() WHERE id = :id"),
            {"id": str(finalized_id)},
        )
    engine.dispose()


def test_downgrade_refused_after_marker_use() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, finalized_id = _raw_seed_consultation(TEST_DATABASE_URL, state="finalized")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE consultations SET author_deleted_at = now() WHERE id = :id"),
            {"id": str(finalized_id)},
        )
    engine.dispose()

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20261019_0006")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("UPDATE consultations SET author_deleted_at = NULL"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20261019_0006")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("consultations")}
    assert "author_deleted_at" not in columns
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")
