import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image
from sqlalchemy import func, select

from app import consultation_service
from app.cleanup import run_cleanup
from app.config import get_settings
from app.consultation_service import (
    ConsultationCapReachedError,
    ConsultationConflictError,
    fingerprint,
    publish_consultation,
    read_consultation_photo,
)
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_service import (
    ImageUnavailableError,
    InactiveSessionError,
    PublicationInvalidError,
    create_upload_session,
    remove_image,
    upload_image,
)

T0 = datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)


def _jpeg_bytes(color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, format="JPEG", quality=90)
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


def _uploaded(db, storage, account_id, session_id, count) -> list[uuid.UUID]:
    ids = []
    for index in range(count):
        image = upload_image(
            db, storage, account_id, session_id, uuid.uuid4(), io.BytesIO(_jpeg_bytes()), now=T0
        )
        ids.append(image.id)
    return ids


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in (
        "CONSULTATION_MIN_PHOTOS",
        "CONSULTATION_MAX_PHOTOS",
        "MAX_OPEN_CONSULTATIONS",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fingerprint_is_stable_and_sensitive_to_order() -> None:
    ids = [uuid.uuid4(), uuid.uuid4()]
    assert fingerprint(ids, "Q", None, "public") == fingerprint(ids, "Q", None, "public")
    assert fingerprint(ids, "Q", None, "public") != fingerprint(
        list(reversed(ids)), "Q", None, "public"
    )
    assert fingerprint(ids, "Q", None, "public") != fingerprint(ids, "Q2", None, "public")
    assert fingerprint(ids, "Q", None, "public") != fingerprint(ids, "Q", None, "private")


def test_fingerprint_has_unambiguous_field_boundaries() -> None:
    ids = [uuid.uuid4(), uuid.uuid4()]
    assert fingerprint(ids, "a\x1fb", "c", "public") != fingerprint(ids, "a", "b\x1fc", "public")


def test_publication_creates_consultation_and_consumes_session(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        consultation = publish_consultation(
            db, storage, account_id, session.id, image_ids, "Which one?", None, "public", now=T0
        )

        assert consultation.state == ConsultationState.open
        session_row = db.get(PhotoUploadSession, session.id)
        assert session_row.state == PhotoUploadSessionState.consumed

        photos = db.scalars(
            select(ConsultationPhoto)
            .where(ConsultationPhoto.consultation_id == consultation.id)
            .order_by(ConsultationPhoto.ordinal)
        ).all()
        assert [photo.image_id for photo in photos] == image_ids


def test_publication_revokes_unselected_images(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 3)
        selected = image_ids[:2]

        publish_consultation(
            db, storage, account_id, session.id, selected, "Q", None, "public", now=T0
        )

        promoted = db.get(PhotoUploadImage, selected[0])
        unselected = db.get(PhotoUploadImage, image_ids[2])
        assert promoted.state.value == "ready"
        assert unselected.state.value == "revoked"
        assert unselected.deletion_requested_at is not None


def test_promoted_files_survive_cleanup(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )

        run_cleanup(db, storage, now=T0 + timedelta(hours=25))

        for image_id in image_ids:
            image = db.get(PhotoUploadImage, image_id)
            assert image is not None and image.storage_key is not None
            assert storage.exists(image.storage_key) is True


def test_publication_rolls_back_on_failure(session_factory, storage, monkeypatch) -> None:
    def boom(db, session_id, selected_ids, now):
        raise RuntimeError("injected failure")

    monkeypatch.setattr(consultation_service, "_revoke_unselected", boom)

    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        with pytest.raises(RuntimeError):
            publish_consultation(
                db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
            )

        db.rollback()
        assert db.scalar(select(Consultation)) is None
        session_row = db.get(PhotoUploadSession, session.id)
        assert session_row.state == PhotoUploadSessionState.active


def test_changed_payload_for_consumed_session_conflicts(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )

        with pytest.raises(ConsultationConflictError):
            publish_consultation(
                db, storage, account_id, session.id, image_ids, "Other", None, "public", now=T0
            )


def test_idempotent_retry_after_consumption(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        first = publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )
        second = publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )

        assert first.id == second.id
        assert db.scalar(select(func.count()).select_from(Consultation)) == 1


def test_service_normalizes_before_persisting_and_fingerprinting(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        first = publish_consultation(
            db,
            storage,
            account_id,
            session.id,
            image_ids,
            "  Which one?  ",
            "  Some context  ",
            "public",
            now=T0,
        )
        second = publish_consultation(
            db,
            storage,
            account_id,
            session.id,
            image_ids,
            "Which one?",
            "Some context",
            "public",
            now=T0,
        )

        assert first.id == second.id
        assert first.question == "Which one?"
        assert first.context == "Some context"


def test_service_rejects_invalid_text_before_publication(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        with pytest.raises(PublicationInvalidError):
            publish_consultation(
                db, storage, account_id, session.id, image_ids, "   ", None, "public", now=T0
            )

        assert db.scalar(select(Consultation)) is None
        assert db.get(PhotoUploadSession, session.id).state == PhotoUploadSessionState.active


def test_cap_reached(session_factory, storage, monkeypatch) -> None:
    monkeypatch.setenv("MAX_OPEN_CONSULTATIONS", "1")
    get_settings.cache_clear()

    with session_factory() as db:
        account_id = _account_id(db)
        first = create_upload_session(db, account_id, now=T0)
        first_ids = _uploaded(db, storage, account_id, first.id, 2)
        publish_consultation(
            db, storage, account_id, first.id, first_ids, "Q", None, "public", now=T0
        )

        second = create_upload_session(db, account_id, now=T0)
        second_ids = _uploaded(db, storage, account_id, second.id, 2)
        with pytest.raises(ConsultationCapReachedError):
            publish_consultation(
                db, storage, account_id, second.id, second_ids, "Q", None, "public", now=T0
            )


def test_expired_session_cannot_publish(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)

        with pytest.raises(InactiveSessionError):
            publish_consultation(
                db,
                storage,
                account_id,
                session.id,
                image_ids,
                "Q",
                None,
                "public",
                now=T0 + timedelta(hours=25),
            )


def test_remove_image_on_consumed_session_is_rejected(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)
        publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )

        with pytest.raises(InactiveSessionError):
            remove_image(db, account_id, session.id, image_ids[0], now=T0)


def test_missing_photo_bytes_yield_retryable_unavailable(session_factory, storage) -> None:
    with session_factory() as db:
        account_id = _account_id(db)
        session = create_upload_session(db, account_id, now=T0)
        image_ids = _uploaded(db, storage, account_id, session.id, 2)
        consultation = publish_consultation(
            db, storage, account_id, session.id, image_ids, "Q", None, "public", now=T0
        )

        photo = db.scalar(
            select(ConsultationPhoto).where(ConsultationPhoto.consultation_id == consultation.id)
        )
        assert photo is not None
        image = db.get(PhotoUploadImage, photo.image_id)
        assert image is not None and image.storage_key is not None
        storage.delete_normalized(image.storage_key)

        with pytest.raises(ImageUnavailableError):
            read_consultation_photo(db, storage, consultation.id, photo.id, account_id, None)
