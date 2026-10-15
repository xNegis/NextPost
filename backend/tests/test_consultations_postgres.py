import io
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.consultation_service import (
    ConsultationCapReachedError,
    publish_consultation,
)
from app.db import Base
from app.models import Account
from app.photo_service import create_upload_session, upload_image
from app.storage import PhotoStorage

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")


def _jpeg_bytes(color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


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


def _session_with_images(pg_factory, storage, account_id) -> tuple[uuid.UUID, list[uuid.UUID]]:
    with pg_factory() as db:
        session = create_upload_session(db, account_id)
        image_ids = []
        for index in range(2):
            image = upload_image(
                db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
            )
            image_ids.append(image.id)
        return session.id, image_ids


def test_two_sessions_race_for_last_slot(pg_factory, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MAX_OPEN_CONSULTATIONS", "1")
    get_settings.cache_clear()
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()

    with pg_factory() as db:
        account_id = _account_id(db)

    first_session, first_ids = _session_with_images(pg_factory, storage, account_id)
    second_session, second_ids = _session_with_images(pg_factory, storage, account_id)

    def publish_one(session_id, image_ids) -> str:
        with pg_factory() as db:
            try:
                publish_consultation(
                    db, storage, account_id, session_id, image_ids, "Q", None, "public"
                )
                return "ok"
            except ConsultationCapReachedError:
                return "cap"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(
                lambda args: publish_one(*args),
                [(first_session, first_ids), (second_session, second_ids)],
            )
        )

    assert sorted(outcomes) == ["cap", "ok"]
