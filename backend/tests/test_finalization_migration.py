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
    """Seed one consultation without photos, compatible with revision 0007."""
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
                "state": state,
                "published_at": datetime(2026, 1, 1, 12, 0, 0),
                "source_session_id": str(session_id),
                "fingerprint": uuid.uuid4().hex[:32],
            },
        )
    engine.dispose()
    return account_id, consultation_id


def _raw_seed_consultation_with_photos(
    url: str, *, state: str = "open"
) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    """Seed a consultation with two photos at head, returning (account, consultation, photos)."""
    suffix = uuid.uuid4().hex[:8]
    account_id = uuid.uuid4()
    session_id = uuid.uuid4()
    consultation_id = uuid.uuid4()
    photo_ids = [uuid.uuid4(), uuid.uuid4()]
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
                "state": state,
                "published_at": datetime(2026, 1, 1, 12, 0, 0),
                "source_session_id": str(session_id),
                "fingerprint": uuid.uuid4().hex[:32],
            },
        )
        for ordinal, photo_id in enumerate(photo_ids):
            image_id = uuid.uuid4()
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
                    "VALUES (:id, :consultation_id, :image_id, :ordinal)"
                ),
                {
                    "id": str(photo_id),
                    "consultation_id": str(consultation_id),
                    "image_id": str(image_id),
                    "ordinal": ordinal,
                },
            )
    engine.dispose()
    return account_id, consultation_id, photo_ids


def test_fresh_upgrade_adds_finalization_schema() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)

    assert "consultation_finalizations" in inspector.get_table_names()
    assert "consultation_final_selections" in inspector.get_table_names()
    assert "consultation_final_option_counts" in inspector.get_table_names()
    assert "consultation_outcomes" in inspector.get_table_names()

    finalization_checks = {
        c["name"] for c in inspector.get_check_constraints("consultation_finalizations")
    }
    assert "ck_finalizations_total_votes" in finalization_checks

    outcome_checks = {c["name"] for c in inspector.get_check_constraints("consultation_outcomes")}
    assert "ck_outcomes_outcome" in outcome_checks

    engine.dispose()


def test_upgrade_from_0007_preserves_finalized_rows_without_backfill() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20261020_0007")

    _, finalized_id = _raw_seed_consultation(TEST_DATABASE_URL, state="finalized")

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM consultation_finalizations WHERE consultation_id = :id"),
            {"id": str(finalized_id)},
        ).scalar_one()
        assert count == 0
    engine.dispose()


def test_composite_fk_rejects_foreign_option() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, first_id, first_photos = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)
    _, second_id, _second_photos = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO consultation_final_selections "
                    "(id, consultation_id, consultation_photo_id, ordinal) "
                    "VALUES (:id, :consultation_id, :photo_id, 0)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "consultation_id": str(first_id),
                    "photo_id": str(_second_photos[0]),
                },
            )
    engine.dispose()


def test_selection_without_header_is_rejected() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, photo_ids = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO consultation_final_selections "
                    "(id, consultation_id, consultation_photo_id, ordinal) "
                    "VALUES (:id, :consultation_id, :photo_id, 0)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "consultation_id": str(consultation_id),
                    "photo_id": str(photo_ids[0]),
                },
            )
    engine.dispose()


def test_option_count_without_header_is_rejected() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, photo_ids = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO consultation_final_option_counts "
                    "(id, consultation_id, consultation_photo_id, ordinal, vote_count) "
                    "VALUES (:id, :consultation_id, :photo_id, 0, 0)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "consultation_id": str(consultation_id),
                    "photo_id": str(photo_ids[0]),
                },
            )
    engine.dispose()


def test_downgrade_refused_after_selection_and_count_use() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, photo_ids = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO consultation_finalizations "
                "(consultation_id, operation_id, payload_fingerprint, finalized_at, total_votes) "
                "VALUES (:consultation_id, :operation_id, :fingerprint, :finalized_at, 0)"
            ),
            {
                "consultation_id": str(consultation_id),
                "operation_id": str(uuid.uuid4()),
                "fingerprint": "x" * 64,
                "finalized_at": datetime(2026, 1, 1, 12, 0, 0),
            },
        )
        conn.execute(
            text(
                "INSERT INTO consultation_final_selections "
                "(id, consultation_id, consultation_photo_id, ordinal) "
                "VALUES (:id, :consultation_id, :photo_id, 0)"
            ),
            {
                "id": str(uuid.uuid4()),
                "consultation_id": str(consultation_id),
                "photo_id": str(photo_ids[0]),
            },
        )
        conn.execute(
            text(
                "INSERT INTO consultation_final_option_counts "
                "(id, consultation_id, consultation_photo_id, ordinal, vote_count) "
                "VALUES (:id, :consultation_id, :photo_id, 0, 0)"
            ),
            {
                "id": str(uuid.uuid4()),
                "consultation_id": str(consultation_id),
                "photo_id": str(photo_ids[0]),
            },
        )
    engine.dispose()

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20261020_0007")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM consultation_final_option_counts"))
        conn.execute(text("DELETE FROM consultation_final_selections"))
        conn.execute(text("DELETE FROM consultation_finalizations"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20261020_0007")
    _run(TEST_DATABASE_URL, "upgrade", "head")


def test_downgrade_refused_after_finalization_use() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, photo_ids = _raw_seed_consultation_with_photos(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO consultation_finalizations "
                "(consultation_id, operation_id, payload_fingerprint, finalized_at, total_votes) "
                "VALUES (:consultation_id, :operation_id, :fingerprint, :finalized_at, 0)"
            ),
            {
                "consultation_id": str(consultation_id),
                "operation_id": str(uuid.uuid4()),
                "fingerprint": "x" * 64,
                "finalized_at": datetime(2026, 1, 1, 12, 0, 0),
            },
        )
    engine.dispose()

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20261020_0007")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM consultation_finalizations"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20261020_0007")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    assert "consultation_finalizations" not in inspector.get_table_names()
    assert "consultation_outcomes" not in inspector.get_table_names()
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")
