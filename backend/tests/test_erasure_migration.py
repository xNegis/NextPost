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
from app.config import get_settings
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
            state=PhotoUploadSessionState.consumed,
            lease_expires_at=datetime(2030, 1, 1),
        )
        db.add(session)
        db.flush()
        images = []
        for index in range(2):
            image = PhotoUploadImage(
                upload_session_id=session.id,
                attempt_id=uuid.uuid4(),
                state="ready",
                storage_key=uuid.uuid4().hex,
                width=64,
                height=64,
            )
            db.add(image)
            db.flush()
            images.append(image)
        consultation_id = uuid.uuid4()
        db.execute(
            text(
                "INSERT INTO consultations (id, owner_id, question, context, audience, state, "
                "published_at, source_session_id, fingerprint, private_link_generation, "
                "private_link_active) VALUES (:id, :owner_id, :question, :context, :audience, "
                ":state, :published_at, :source_session_id, :fingerprint, 0, false)"
            ),
            {
                "id": str(consultation_id),
                "owner_id": str(owner.id),
                "question": "Q",
                "context": None,
                "audience": "public",
                "state": ConsultationState.open.value,
                "published_at": datetime(2026, 1, 1, 12, 0, 0),
                "source_session_id": str(session.id),
                "fingerprint": uuid.uuid4().hex[:32],
            },
        )

        # Insert ordered photos with raw SQL so the seed also works at revision 0005, before
        # consultation_photos.media_deleted_at exists.
        for image, ordinal in ((images[0], 0), (images[1], 1)):
            db.execute(
                text(
                    "INSERT INTO consultation_photos (id, consultation_id, image_id, ordinal) "
                    "VALUES (:id, :c, :i, :o)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "c": str(consultation_id),
                    "i": str(image.id),
                    "o": ordinal,
                },
            )
        db.commit()
        photo_ids = [
            row[0]
            for row in db.execute(
                text(
                    "SELECT id FROM consultation_photos WHERE consultation_id = :c ORDER BY ordinal"
                ),
                {"c": str(consultation_id)},
            ).all()
        ]
        return owner.id, consultation_id, photo_ids


def _seed_vote(url: str, consultation_id: uuid.UUID, photo_id: uuid.UUID) -> None:
    engine = create_engine(url)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        voter = Account(
            email=f"voter{uuid.uuid4().hex[:8]}@example.com",
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
                "p": str(photo_id),
            },
        )
        db.commit()


def test_fresh_upgrade_adds_media_erasure_schema() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)

    consultation_columns = {c["name"]: c for c in inspector.get_columns("consultations")}
    assert consultation_columns["question"]["nullable"] is True
    assert consultation_columns["audience"]["nullable"] is True
    assert consultation_columns["source_session_id"]["nullable"] is True
    assert consultation_columns["fingerprint"]["nullable"] is True

    photo_columns = {c["name"]: c for c in inspector.get_columns("consultation_photos")}
    assert photo_columns["image_id"]["nullable"] is True
    assert "media_deleted_at" in photo_columns

    checks = {c["name"] for c in inspector.get_check_constraints("consultations")}
    assert "ck_consultations_open_complete" in checks
    photo_checks = {c["name"] for c in inspector.get_check_constraints("consultation_photos")}
    assert "ck_consultation_photos_media" in photo_checks
    engine.dispose()


def test_upgrade_from_0005_preserves_open_consultation_and_vote() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "20261016_0005")

    owner_id, consultation_id, photo_ids = _seed_consultation(TEST_DATABASE_URL)
    _seed_vote(TEST_DATABASE_URL, consultation_id, photo_ids[0])

    _run(TEST_DATABASE_URL, "upgrade", "head")

    engine = create_engine(TEST_DATABASE_URL)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        consultation = db.get(Consultation, consultation_id)
        assert consultation is not None
        assert consultation.owner_id == owner_id
        assert consultation.state == ConsultationState.open
        assert consultation.question == "Q"
        assert consultation.audience == "public"
        assert consultation.source_session_id is not None
        assert consultation.fingerprint is not None
        vote_count = db.execute(
            text("SELECT count(*) FROM votes WHERE consultation_id = :c"),
            {"c": str(consultation_id)},
        ).scalar_one()
        assert vote_count == 1
    engine.dispose()


def test_open_complete_constraint_rejects_null_fields() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE consultations SET question = NULL WHERE id = :c"),
                {"c": str(consultation_id)},
            )
    engine.dispose()


def test_photo_media_check_requires_detach_marker() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as db:
        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    "INSERT INTO consultation_photos (id, consultation_id, image_id, ordinal, "
                    "media_deleted_at) VALUES (:id, :c, NULL, 9, NULL)"
                ),
                {"id": str(uuid.uuid4()), "c": str(consultation_id)},
            )
            db.commit()
        db.rollback()
    engine.dispose()


def test_open_consultation_rejects_photo_detach() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE consultation_photos SET image_id = NULL, media_deleted_at = now() "
                    "WHERE consultation_id = :c"
                ),
                {"c": str(consultation_id)},
            )
    engine.dispose()


def test_terminal_consultation_allows_verified_detach() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE consultations SET state = 'deleted' WHERE id = :c"),
            {"c": str(consultation_id)},
        )
        conn.execute(
            text(
                "UPDATE consultation_photos SET image_id = NULL, media_deleted_at = now() "
                "WHERE consultation_id = :c"
            ),
            {"c": str(consultation_id)},
        )

    with engine.connect() as conn:
        detached = conn.execute(
            text(
                "SELECT count(*) FROM consultation_photos "
                "WHERE consultation_id = :c AND image_id IS NULL"
            ),
            {"c": str(consultation_id)},
        ).scalar_one()
    assert detached == 2
    engine.dispose()


def test_downgrade_refused_after_detach_and_sanitization() -> None:
    assert TEST_DATABASE_URL is not None
    _reset_schema(TEST_DATABASE_URL)
    _run(TEST_DATABASE_URL, "upgrade", "head")

    _, consultation_id, _ = _seed_consultation(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        # Terminalize first: the open-media constraint trigger forbids detaching a photo while
        # the parent consultation is open.
        conn.execute(
            text("UPDATE consultations SET state = 'deleted' WHERE id = :c"),
            {"c": str(consultation_id)},
        )
        conn.execute(
            text(
                "UPDATE consultation_photos SET image_id = NULL, media_deleted_at = now() "
                "WHERE consultation_id = :c"
            ),
            {"c": str(consultation_id)},
        )
    engine.dispose()

    with pytest.raises(RuntimeError):
        _run(TEST_DATABASE_URL, "downgrade", "20261016_0005")

    # Clearing the irreversible indicator makes downgrade possible again.
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM consultation_photos WHERE image_id IS NULL"))
    engine.dispose()

    _run(TEST_DATABASE_URL, "downgrade", "20261016_0005")

    engine = create_engine(TEST_DATABASE_URL)
    inspector = inspect(engine)
    photo_columns = {c["name"] for c in inspector.get_columns("consultation_photos")}
    assert "media_deleted_at" not in photo_columns
    engine.dispose()

    _run(TEST_DATABASE_URL, "upgrade", "head")
