import io
import uuid

import pytest
from PIL import Image
from sqlalchemy import select

from app.config import get_settings
from app.models import Account, PhotoImageState, PhotoUploadImage
from app.photo_service import (
    NotFoundError,
    PublicationInvalidError,
    create_upload_session,
    remove_image,
    upload_image,
    validate_publication_images,
)


def _jpeg_bytes(size=(64, 64), color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _account_id(db) -> uuid.UUID:
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


def _ready_ids(db, session_id: uuid.UUID, count: int) -> list[uuid.UUID]:
    ids = []
    for _ in range(count):
        row = PhotoUploadImage(
            upload_session_id=session_id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=uuid.uuid4().hex,
            width=10,
            height=10,
            byte_length=10,
        )
        db.add(row)
        db.flush()
        ids.append(row.id)
    db.commit()
    return ids


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in ("CONSULTATION_MIN_PHOTOS", "CONSULTATION_MAX_PHOTOS"):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_validates_ordered_ready_ids(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        first = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )
        second = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )

        images = validate_publication_images(
            db, storage, account_id, session.id, [first.id, second.id]
        )

        assert [image.id for image in images] == [first.id, second.id]


def test_rejects_wrong_owner(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        other_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )

        with pytest.raises(NotFoundError):
            validate_publication_images(db, storage, other_id, session.id, [image.id])


def test_rejects_duplicate_ids(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, [image.id, image.id])


def test_rejects_revoked_image(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )
        remove_image(db, account_id, session.id, image.id)

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, [image.id])


def test_rejects_missing_storage_key(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image_id = _ready_ids(db, session.id, 1)[0]
        row = db.scalar(select(PhotoUploadImage).where(PhotoUploadImage.id == image_id))
        assert row is not None
        row.storage_key = None
        db.commit()

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, [image_id])


def test_rejects_ready_image_with_missing_bytes(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        image = upload_image(
            db, storage, account_id, session.id, uuid.uuid4(), io.BytesIO(_jpeg_bytes())
        )
        row = db.get(PhotoUploadImage, image.id)
        assert row is not None and row.storage_key is not None
        storage.delete_normalized(row.storage_key)

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, [image.id])


def test_rejects_below_minimum(monkeypatch, session_factory, storage) -> None:
    monkeypatch.setenv("CONSULTATION_MIN_PHOTOS", "3")
    get_settings.cache_clear()
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        ids = _ready_ids(db, session.id, 2)

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, ids)


def test_rejects_above_maximum(monkeypatch, session_factory, storage) -> None:
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "5")
    get_settings.cache_clear()
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id)
        ids = _ready_ids(db, session.id, 6)

        with pytest.raises(PublicationInvalidError):
            validate_publication_images(db, storage, account_id, session.id, ids)
