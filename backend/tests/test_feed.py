import base64
import io
import json
import uuid
from datetime import datetime, timedelta

import pytest
from PIL import Image
from sqlalchemy import select

from app import consultation_service
from app.config import get_settings
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)

VALID_PASSWORD = "correct-horse-battery-staple"


def _jpeg_bytes(size=(64, 64), color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def register(client, email="ana@example.com", alias="Ana") -> None:
    response = client.post(
        "/api/accounts",
        json={"email": email, "alias": alias, "password": VALID_PASSWORD},
    )
    assert response.status_code == 201


def create_session(client) -> str:
    response = client.post("/api/photo-upload-sessions")
    assert response.status_code == 201
    return response.json()["id"]


def upload(client, session_id: str) -> str:
    response = client.post(
        f"/api/photo-upload-sessions/{session_id}/images",
        files={"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"attempt_id": str(uuid.uuid4())},
    )
    assert response.status_code == 201
    return response.json()["id"]


def publishable_session(client, count: int = 2) -> tuple[str, list[str]]:
    session_id = create_session(client)
    image_ids = [upload(client, session_id) for _ in range(count)]
    return session_id, image_ids


def publish(
    client, session_id, image_ids, *, audience="public", question="Which one?", context=None
):
    return client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": question,
            "context": context,
            "audience": audience,
        },
    )


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in (
        "CONSULTATION_MIN_PHOTOS",
        "CONSULTATION_MAX_PHOTOS",
        "MAX_OPEN_CONSULTATIONS",
        "CONSULTATION_QUESTION_MAX_LENGTH",
        "CONSULTATION_CONTEXT_MAX_LENGTH",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _new_account(db, email="ana@example.com", alias="Ana") -> Account:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=email if "@" in email else f"a{suffix}@example.com",
        alias=alias,
        alias_canonical=alias.lower(),
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account


def _new_session(db, account_id: uuid.UUID) -> PhotoUploadSession:
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.active,
        lease_expires_at=datetime(2030, 1, 1, tzinfo=None),
    )
    db.add(session)
    db.commit()
    return session


def _insert_consultation(
    db,
    account_id,
    published_at,
    *,
    state="open",
    audience="public",
    question="Which one?",
    context=None,
) -> Consultation:
    session = _new_session(db, account_id)
    consultation = Consultation(
        owner_id=account_id,
        question=question,
        context=context,
        audience=audience,
        state=ConsultationState(state),
        published_at=published_at,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
        private_link_generation=1 if audience == "private" else 0,
        private_link_active=audience == "private",
    )
    db.add(consultation)
    db.commit()
    return consultation


def _insert_public_consultation(
    db, account_id, published_at, *, question="Which one?", context=None
) -> Consultation:
    consultation = _insert_consultation(
        db,
        account_id,
        published_at,
        question=question,
        context=context,
    )
    image = PhotoUploadImage(
        upload_session_id=consultation.source_session_id,
        attempt_id=uuid.uuid4(),
        state="ready",
        storage_key=f"k{uuid.uuid4().hex[:12]}",
        width=64,
        height=64,
    )
    db.add(image)
    db.flush()
    db.add(ConsultationPhoto(consultation_id=consultation.id, image_id=image.id, ordinal=0))
    db.commit()
    return consultation


def _set_state(session_factory, consultation_id: str, state: str) -> None:
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()


def _account_id(db, email="ana@example.com", alias="Ana") -> uuid.UUID:
    return _new_account(db, email=email, alias=alias).id


def test_feed_requires_authentication(client) -> None:
    assert client.get("/api/consultations/feed").status_code == 401


def test_feed_empty_collection_is_distinct_from_failure(client) -> None:
    register(client)
    response = client.get("/api/consultations/feed")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}


def test_feed_read_headers_are_present(client) -> None:
    register(client)
    response = client.get("/api/consultations/feed")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_feed_includes_own_public_with_owner_marker(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    response = client.get("/api/consultations/feed")
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == {
        "id",
        "owner_nickname",
        "question",
        "context_excerpt",
        "audience",
        "state",
        "published_at",
        "is_owner",
        "has_voted",
        "first_photo",
    }
    assert item["id"] == consultation_id
    assert item["owner_nickname"] == "Ana"
    assert item["question"] == "Which one?"
    assert item["context_excerpt"] is None
    assert item["audience"] == "public"
    assert item["state"] == "open"
    assert item["is_owner"] is True
    assert item["published_at"].endswith("Z")
    assert set(item["first_photo"]) == {"id", "width", "height"}
    assert item["first_photo"]["width"] > 0
    assert item["first_photo"]["height"] > 0


def test_feed_includes_other_public_as_not_owner(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    publish(client, session_id, image_ids)

    register(client, email="bob@example.com", alias="Bob")

    response = client.get("/api/consultations/feed")
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["owner_nickname"] == "Ana"
    assert item["is_owner"] is False


def test_feed_excludes_private_for_owner_and_token_holder(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]
    token = client.get(f"/api/consultations/{consultation_id}/private-link").json()["token"]

    assert client.get("/api/consultations/feed").json()["items"] == []

    register(client, email="bob@example.com", alias="Bob")
    response = client.get("/api/consultations/feed", headers={"X-NextPost-Private-Link": token})
    assert response.json()["items"] == []


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_feed_excludes_terminal_rows(client, session_factory, state) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    _set_state(session_factory, consultation_id, state)

    assert client.get("/api/consultations/feed").json()["items"] == []


def test_feed_excludes_unpublished_upload_sessions(client) -> None:
    register(client)
    create_session(client)

    assert client.get("/api/consultations/feed").json()["items"] == []


def test_feed_context_excerpt_truncates_with_ellipsis(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        _insert_public_consultation(
            db, account_id, datetime(2026, 1, 1, 12, 0, 0), context="x" * 200
        )

    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["context_excerpt"] == "x" * 160 + "…"


def test_feed_context_excerpt_short_is_untruncated(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        _insert_public_consultation(db, account_id, datetime(2026, 1, 1, 12, 0, 0), context="short")

    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["context_excerpt"] == "short"


def test_feed_first_photo_is_lowest_stored_ordinal(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client, count=3)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    detail = client.get(f"/api/consultations/{consultation_id}").json()
    first_detail_photo = detail["photos"][0]["id"]

    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["first_photo"]["id"] == first_detail_photo


def test_feed_paginates_newest_first(client, session_factory) -> None:
    register(client, email="ana@example.com", alias="Ana")
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        base = datetime(2026, 1, 1, 12, 0, 0)
        for index in range(25):
            _insert_public_consultation(
                db, account_id, base + timedelta(minutes=index), question=f"Q{index}"
            )

    first = client.get("/api/consultations/feed?limit=20")
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 20
    assert first_body["next_cursor"] is not None
    assert [item["question"] for item in first_body["items"]] == [
        f"Q{index}" for index in range(24, 4, -1)
    ]

    second = client.get(f"/api/consultations/feed?limit=20&cursor={first_body['next_cursor']}")
    assert second.status_code == 200
    second_body = second.json()
    assert [item["question"] for item in second_body["items"]] == [
        f"Q{index}" for index in range(4, -1, -1)
    ]
    assert second_body["next_cursor"] is None


def test_feed_cursor_ties_do_not_duplicate_or_skip(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        ids = [_insert_public_consultation(db, account_id, published_at).id for _ in range(3)]

    collected: list[str] = []
    cursor = None
    while True:
        url = "/api/consultations/feed?limit=1"
        if cursor is not None:
            url += f"&cursor={cursor}"
        body = client.get(url).json()
        collected.extend(item["id"] for item in body["items"])
        if body["next_cursor"] is None:
            break
        cursor = body["next_cursor"]

    assert len(collected) == len(set(collected)) == 3
    assert set(collected) == {str(i) for i in ids}


def test_feed_malformed_cursor_is_rejected(client) -> None:
    register(client)
    for cursor in ("not-base64!!!", "a" * 600, "%%%"):
        response = client.get(f"/api/consultations/feed?cursor={cursor}")
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "validation_error"


def test_feed_owner_list_cursor_is_rejected(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    publish(client, session_id, image_ids)
    owner_cursor = client.get("/api/my-consultations?state=open&limit=1").json()["next_cursor"]
    assert owner_cursor is None  # fewer than 20 rows produce no cursor

    response = client.get(
        "/api/consultations/feed?cursor="
        + base64.urlsafe_b64encode(
            json.dumps(["v1", "open", "2026-01-01T12:00:00", str(uuid.uuid4())]).encode()
        )
        .decode()
        .rstrip("=")
    )
    assert response.status_code == 422


def test_feed_cursor_with_wrong_version_is_rejected(client) -> None:
    register(client)
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(["v9", "2026-01-01T12:00:00", str(uuid.uuid4())]).encode()
        )
        .decode()
        .rstrip("=")
    )
    response = client.get(f"/api/consultations/feed?cursor={payload}")
    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 51])
def test_feed_limit_bounds_are_enforced(client, limit) -> None:
    register(client)
    response = client.get(f"/api/consultations/feed?limit={limit}")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_feed_corrupt_first_photo_metadata_is_retryable_503(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        _insert_consultation(db, account_id, datetime(2026, 1, 1, 12, 0, 0))

    response = client.get("/api/consultations/feed")
    assert response.status_code == 503
    assert response.json() == {"detail": {"code": "unavailable"}}
    assert response.headers["cache-control"] == "private, no-store"


def test_list_feed_is_set_based_without_storage_or_detail(session_factory, storage) -> None:
    from sqlalchemy.orm import Session as OrmSession

    def no_full_row_get(self, entity, *args, **kwargs):
        raise AssertionError("db.get must not load full rows for a feed read")

    with session_factory() as db:
        owner = _new_account(db)
        other = _new_account(db, email="other@example.com", alias="Other")
        session = _new_session(db, owner.id)
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
        db.add(ConsultationPhoto(consultation_id=consultation.id, image_id=image.id, ordinal=0))
        db.commit()

        original_get = OrmSession.get
        OrmSession.get = no_full_row_get  # type: ignore[method-assign]
        try:
            result = consultation_service.list_feed(db, other.id, 20, None)
        finally:
            OrmSession.get = original_get  # type: ignore[method-assign]

    assert len(result.items) == 1
    assert result.items[0].is_owner is False
    assert result.items[0].owner_nickname == "Ana"
    assert result.items[0].first_photo.width == 64


def test_list_feed_uses_lowest_ordinal_not_client_order(session_factory) -> None:
    with session_factory() as db:
        owner = _new_account(db)
        session = _new_session(db, owner.id)
        image_a = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state="ready",
            storage_key="a",
            width=10,
            height=10,
        )
        image_b = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state="ready",
            storage_key="b",
            width=20,
            height=20,
        )
        db.add_all([image_a, image_b])
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
        db.add(ConsultationPhoto(consultation_id=consultation.id, image_id=image_b.id, ordinal=1))
        db.add(ConsultationPhoto(consultation_id=consultation.id, image_id=image_a.id, ordinal=0))
        db.commit()

        result = consultation_service.list_feed(db, owner.id, 20, None)

    assert result.items[0].first_photo.width == 10
