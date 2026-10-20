"""Disposable RF-37 restart/startup and restore-into-empty-volume validation.

This script proves two operational scenarios against a disposable PostgreSQL database and a
repository-internal temporary photo volume:

1. **Restart/startup recovery**: a terminal consumer commits database revocation with the files
   still on disk (a crash before physical cleanup), then a fresh ``python -m app.cleanup`` process
   (what startup runs) converges the storage and minimizes the ledger.
2. **Database-plus-empty-volume restore**: the same terminal commit is retained in PostgreSQL but
   the photo volume is emptied (the only supported POC restore), and reconciliation treats the
   missing bytes as idempotent absence without resurrecting access.

Run from the repository root with the disposable database reachable on 127.0.0.1:55437 using the
repository virtual environment:

    .venv/Scripts/python harness/validation/rf37_restart_restore_validation.py

It uses only 127.0.0.1 and a temporary directory under ``backend/`` that is removed afterwards.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
PHOTO_DIR = BACKEND_DIR / ".rf37-validation-photos"

DATABASE_URL = os.getenv(
    "RF37_VALIDATION_DATABASE_URL",
    "postgresql+psycopg://nextpost:nextpost-test-only@127.0.0.1:55437/nextpost_test",
)

sys.path.insert(0, str(BACKEND_DIR))

from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_erasure_service import mark_media_for_erasure
from app.storage import PhotoStorage
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

T0 = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = DATABASE_URL
    env["PHOTO_STORAGE_ROOT"] = str(PHOTO_DIR)
    env["APP_ENV"] = "development"
    env["PRIVATE_LINK_SECRET"] = ""
    return env


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=str(BACKEND_DIR), env=_env(), capture_output=True, text=True, check=False
    )


def _reset_schema() -> None:
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()


def _factory() -> sessionmaker[Session]:
    engine = create_engine(DATABASE_URL)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def _account_id(db: Session) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"v{suffix}@example.com",
        alias=f"V{suffix}",
        alias_canonical=f"v{suffix}",
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account.id


def _publish_and_terminalize(db: Session, storage: PhotoStorage) -> tuple[uuid.UUID, list[str]]:
    account_id = _account_id(db)
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    db.add(session)
    db.flush()
    keys: list[str] = []
    image_ids: list[uuid.UUID] = []
    for _ in range(2):
        key = uuid.uuid4().hex
        storage.write_normalized(key, b"x")
        keys.append(key)
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=key,
            width=10,
            height=10,
        )
        db.add(image)
        db.flush()
        image_ids.append(image.id)
    consultation = Consultation(
        owner_id=account_id,
        question="Q",
        context=None,
        audience="public",
        state=ConsultationState.open,
        published_at=T0,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
    )
    db.add(consultation)
    db.flush()
    for ordinal, image_id in enumerate(image_ids):
        db.add(
            ConsultationPhoto(consultation_id=consultation.id, image_id=image_id, ordinal=ordinal)
        )
    db.commit()

    # Terminal consumer: lock, mark for erasure, write terminal state, commit once.
    locked = db.execute(
        select(Consultation).where(Consultation.id == consultation.id).with_for_update()
    ).scalar_one()
    mark_media_for_erasure(db, locked, now=T0)
    locked.state = ConsultationState.deleted
    db.commit()
    return consultation.id, keys


def _assert_minimized(db: Session, consultation_id: uuid.UUID, keys: list[str], storage: PhotoStorage) -> None:
    consultation = db.get(Consultation, consultation_id)
    assert consultation.source_session_id is None, "source session not detached"
    photos = db.scalars(
        select(ConsultationPhoto).where(ConsultationPhoto.consultation_id == consultation_id)
    ).all()
    assert photos, "stable options must survive"
    assert all(photo.image_id is None and photo.media_deleted_at is not None for photo in photos)
    for key in keys:
        assert storage.exists(key) is False, f"storage key still present: {key}"


def main() -> int:
    if PHOTO_DIR.exists():
        shutil.rmtree(PHOTO_DIR)
    PHOTO_DIR.mkdir(parents=True)
    storage = PhotoStorage(PHOTO_DIR)
    storage.ensure_dirs()

    try:
        _reset_schema()
        migrated = _run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"])
        assert migrated.returncode == 0, migrated.stderr

        factory = _factory()

        # --- Scenario 1: restart/startup recovery -----------------------------------------
        with factory() as db:
            consultation_id, keys = _publish_and_terminalize(db, storage)
            for key in keys:
                assert storage.exists(key) is True, "files must still exist before cleanup"

        cleanup = _run([sys.executable, "-m", "app.cleanup"])
        assert cleanup.returncode == 0, cleanup.stdout + cleanup.stderr
        assert "terminal_sessions_completed=1" in cleanup.stdout, cleanup.stdout

        with factory() as db:
            _assert_minimized(db, consultation_id, keys, storage)
        print("PASS: restart/startup recovery converged physical deletion")

        # --- Scenario 2: database-plus-empty-volume restore -------------------------------
        with factory() as db:
            consultation_id, keys = _publish_and_terminalize(db, storage)
            for key in keys:
                assert storage.exists(key) is True

        # Simulate restoring PostgreSQL into a NEW EMPTY photo volume (the only supported restore).
        for child in PHOTO_DIR.rglob("*"):
            if child.is_file():
                child.unlink()
        for key in keys:
            assert storage.exists(key) is False

        cleanup = _run([sys.executable, "-m", "app.cleanup"])
        assert cleanup.returncode == 0, cleanup.stdout + cleanup.stderr
        assert "terminal_sessions_completed=1" in cleanup.stdout, cleanup.stdout

        with factory() as db:
            consultation = db.get(Consultation, consultation_id)
            assert consultation.state == ConsultationState.deleted
            _assert_minimized(db, consultation_id, keys, storage)
        print("PASS: empty-volume restore reconciled idempotently without resurrecting access")

        return 0
    finally:
        shutil.rmtree(PHOTO_DIR, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
