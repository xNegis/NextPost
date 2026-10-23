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
    getattr(command, action)(_config(url), revision)
    get_settings.cache_clear()


def _seed_consultation(url: str, *, state: str = "removed") -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    account_id = uuid.uuid4()
    session_id = uuid.uuid4()
    consultation_id = uuid.uuid4()
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO accounts (id, email, alias, alias_canonical, password_hash) "
                "VALUES (:id, :email, :alias, :canonical, 'x')"
            ),
            {
                "id": str(account_id),
                "email": f"owner{suffix}@example.com",
                "alias": f"Owner{suffix}",
                "canonical": f"owner{suffix}",
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
                "INSERT INTO consultations (id, owner_id, question, audience, state, published_at, "
                "source_session_id, fingerprint, private_link_generation, private_link_active) "
                "VALUES (:id, :owner_id, :question, 'public', :state, :published_at, :session_id, "
                ":fingerprint, 0, false)"
            ),
            {
                "id": str(consultation_id),
                "owner_id": str(account_id),
                "question": "Historical question" if state == "open" else None,
                "state": state,
                "published_at": datetime(2026, 1, 1),
                "session_id": str(session_id),
                "fingerprint": uuid.uuid4().hex if state == "open" else None,
            },
        )
    engine.dispose()
    return consultation_id


def test_fresh_upgrade_creates_constrained_removal_table() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    assert "consultation_removals" in inspector.get_table_names()
    columns = {column["name"]: column for column in inspector.get_columns("consultation_removals")}
    assert set(columns) == {
        "consultation_id",
        "operation_id",
        "removed_at",
        "operator_id",
        "reason_code",
        "previous_state",
    }
    assert all(not column["nullable"] for column in columns.values())
    checks = {check["name"] for check in inspector.get_check_constraints("consultation_removals")}
    assert checks == {
        "ck_consultation_removals_operator_id",
        "ck_consultation_removals_previous_state",
        "ck_consultation_removals_reason_code",
    }
    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("consultation_removals")
    }
    assert "uq_consultation_removals_operation_id" in unique_names
    engine.dispose()


def test_upgrade_does_not_fabricate_historical_removal_audit() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20261021_0009")
    consultation_id = _seed_consultation(TEST_DATABASE_URL)

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM consultation_removals")).scalar_one() == 0
        state = conn.execute(
            text("SELECT state FROM consultations WHERE id = :id"),
            {"id": str(consultation_id)},
        ).scalar_one()
        assert state == "removed"
    engine.dispose()


def test_downgrade_is_empty_only_and_refuses_after_use() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")
    consultation_id = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO consultation_removals "
                "(consultation_id, operation_id, removed_at, operator_id, reason_code, "
                "previous_state) VALUES (:consultation_id, :operation_id, :removed_at, "
                "'ops.alice', 'other', 'open')"
            ),
            {
                "consultation_id": str(consultation_id),
                "operation_id": str(uuid.uuid4()),
                "removed_at": datetime(2026, 10, 23),
            },
        )
    engine.dispose()

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20261021_0009")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM consultation_removals"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20261021_0009")
    engine = create_engine(TEST_DATABASE_URL)
    assert "consultation_removals" not in inspect(engine).get_table_names()
    engine.dispose()
    _run(TEST_DATABASE_URL, "upgrade", "head")
