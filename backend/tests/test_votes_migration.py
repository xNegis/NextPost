import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.models import (
    Account,
    Consultation,
    ConsultationState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)

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
    from app.config import get_settings

    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    config = _config(url)
    getattr(command, action)(config, revision)
    get_settings.cache_clear()


def _seed_consultation(url: str) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    suffix = uuid.uuid4().hex[:8]
    engine = create_engine(url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        owner = Account(
            email=f"owner{suffix}@example.com",
            alias=f"Owner{suffix}",
            alias_canonical=f"owner{suffix}",
            password_hash="x",
        )
        db.add(owner)
        db.flush()
        session = PhotoUploadSession(
            account_id=owner.id,
            state=PhotoUploadSessionState.active,
            lease_expires_at=datetime(2030, 1, 1),
        )
        db.add(session)
        db.flush()
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state="ready",
            storage_key="k",
            width=64,
            height=64,
        )
        db.add(image)
        db.flush()
        second_image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state="ready",
            storage_key="k2",
            width=64,
            height=64,
        )
        db.add(second_image)
        db.flush()
        consultation = Consultation(
            owner_id=owner.id,
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
        # Insert ordered photos with raw SQL so the seed remains compatible with later revisions
        # that add consultation_photos columns (RF-37 adds media_deleted_at).
        photo_id = uuid.uuid4()
        second_photo_id = uuid.uuid4()
        db.execute(
            text(
                "INSERT INTO consultation_photos (id, consultation_id, image_id, ordinal) "
                "VALUES (:id, :c, :i, 0), (:id2, :c, :i2, 1)"
            ),
            {
                "id": str(photo_id),
                "id2": str(second_photo_id),
                "c": str(consultation.id),
                "i": str(image.id),
                "i2": str(second_image.id),
            },
        )
        db.commit()
        return owner.id, consultation.id, [photo_id, second_photo_id]
    # unreachable; keep mypy/readability honest
    raise AssertionError


def _seed_vote(url: str) -> None:
    _, consultation_id, photo_ids = _seed_consultation(url)
    engine = create_engine(url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        voter = Account(
            email="voter@example.com",
            alias="Voter",
            alias_canonical="voter",
            password_hash="x",
        )
        db.add(voter)
        db.commit()
        db.execute(
            text(
                "INSERT INTO votes (id, consultation_id, voter_id, consultation_photo_id) "
                "VALUES (:id, :c, :v, :p)"
            ),
            {
                "id": str(uuid.uuid4()),
                "c": str(consultation_id),
                "v": str(voter.id),
                "p": str(photo_ids[0]),
            },
        )
        db.commit()


def test_fresh_upgrade_creates_vote_schema() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "votes" in tables

    vote_columns = {col["name"] for col in inspector.get_columns("votes")}
    assert {
        "id",
        "consultation_id",
        "voter_id",
        "consultation_photo_id",
        "created_at",
    } <= vote_columns

    unique_constraints = inspector.get_unique_constraints("votes")
    assert any(
        set(uc["column_names"]) == {"consultation_id", "voter_id"} for uc in unique_constraints
    )

    photo_constraints = inspector.get_unique_constraints("consultation_photos")
    assert any(set(uc["column_names"]) == {"consultation_id", "id"} for uc in photo_constraints)

    vote_indexes = {idx["name"] for idx in inspector.get_indexes("votes")}
    assert "ix_votes_consultation_photo" in vote_indexes
    engine.dispose()


def test_upgrade_from_0004_preserves_existing_consultations() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20260928_0004")

    owner_id, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        consultation = db.get(Consultation, consultation_id)
        assert consultation is not None
        assert consultation.owner_id == owner_id
        assert consultation.state == ConsultationState.open
    engine.dispose()


def test_direct_sql_rejects_duplicate_vote_and_cross_consultation_option() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    _, consultation_id, photo_ids = _seed_consultation(TEST_DATABASE_URL)
    _, _, other_photo_ids = _seed_consultation(TEST_DATABASE_URL)

    with factory() as db:
        voter = Account(
            email="voter@example.com",
            alias="Voter",
            alias_canonical="voter",
            password_hash="x",
        )
        db.add(voter)
        db.commit()

        insert = (
            "INSERT INTO votes (id, consultation_id, voter_id, consultation_photo_id) "
            "VALUES (:id, :c, :v, :p)"
        )
        db.execute(
            text(insert),
            {
                "id": str(uuid.uuid4()),
                "c": str(consultation_id),
                "v": str(voter.id),
                "p": str(photo_ids[0]),
            },
        )
        db.commit()

        with pytest.raises(IntegrityError):
            db.execute(
                text(insert),
                {
                    "id": str(uuid.uuid4()),
                    "c": str(consultation_id),
                    "v": str(voter.id),
                    "p": str(photo_ids[1]),
                },
            )
            db.commit()
        db.rollback()

        with pytest.raises(IntegrityError):
            db.execute(
                text(insert),
                {
                    "id": str(uuid.uuid4()),
                    "c": str(consultation_id),
                    "v": str(voter.id),
                    "p": str(other_photo_ids[0]),
                },
            )
            db.commit()
        db.rollback()
    engine.dispose()


def test_populated_downgrade_is_refused_and_empty_downgrade_succeeds() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _seed_vote(TEST_DATABASE_URL)

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20260928_0004")

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM votes"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20260928_0004")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    assert "votes" not in inspector.get_table_names()
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")
    engine = create_engine(TEST_DATABASE_URL)
    assert "votes" in inspect(engine).get_table_names()
    engine.dispose()
