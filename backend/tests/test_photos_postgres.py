import io
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.cleanup import run_cleanup
from app.config import get_settings
from app.db import Base
from app.models import Account, PhotoImageState, PhotoUploadImage
from app.photo_service import (
    PhotoLimitReachedError,
    create_upload_session,
    discard_upload_session,
    upload_image,
)
from app.storage import PhotoStorage

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 30, 30)).save(buffer, format="JPEG", quality=90)
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


def test_concurrent_uploads_never_exceed_maximum(pg_factory, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "5")
    get_settings.cache_clear()
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()

    with pg_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)

    def upload_once() -> str:
        with pg_factory() as db:
            try:
                result = upload_image(
                    db,
                    storage,
                    account_id,
                    session.id,
                    uuid.uuid4(),
                    io.BytesIO(_jpeg_bytes()),
                )
                return f"ok:{result.id}"
            except PhotoLimitReachedError:
                return "limit"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(lambda _: upload_once(), range(8)))

    assert outcomes.count("limit") == 3
    assert sum(1 for outcome in outcomes if outcome.startswith("ok:")) == 5


def test_same_attempt_id_is_idempotent_under_concurrency(pg_factory, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "5")
    get_settings.cache_clear()
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()

    with pg_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)

    attempt_id = uuid.uuid4()

    def upload_once() -> str:
        with pg_factory() as db:
            result = upload_image(
                db, storage, account_id, session.id, attempt_id, io.BytesIO(_jpeg_bytes())
            )
            return str(result.id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: upload_once(), range(2)))

    assert len(set(outcomes)) == 1


def test_concurrent_cleanup_claims_a_revoked_image_once(pg_factory, tmp_path) -> None:
    storage = PhotoStorage(tmp_path / "photos")
    storage.ensure_dirs()

    with pg_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image = upload_image(
            db,
            storage,
            account_id,
            session.id,
            uuid.uuid4(),
            io.BytesIO(_jpeg_bytes()),
        )
        row = db.get(PhotoUploadImage, image.id)
        assert row is not None and row.storage_key is not None
        key = row.storage_key
        discard_upload_session(db, account_id, session.id)

    barrier = Barrier(2)

    def cleanup_once() -> int:
        with pg_factory() as db:
            barrier.wait()
            return run_cleanup(db, storage).deleted_files

    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(lambda _: cleanup_once(), range(2)))

    with pg_factory() as db:
        row = db.get(PhotoUploadImage, image.id)
        assert row is not None
        assert row.state == PhotoImageState.deleted
    assert storage.exists(key) is False
    assert sum(reports) == 1
