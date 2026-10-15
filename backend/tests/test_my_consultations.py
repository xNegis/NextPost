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
    ConsultationState,
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
) -> Consultation:
    session = _new_session(db, account_id)
    consultation = Consultation(
        owner_id=account_id,
        question=question,
        context=None,
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


def _set_state(session_factory, consultation_id: str, state: str) -> None:
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()


def test_my_consultations_require_authentication(client) -> None:
    assert client.get("/api/my-consultations").status_code == 401
    assert client.get(f"/api/my-consultations/{uuid.uuid4()}").status_code == 401


def test_empty_collections_are_distinct_from_failure(client) -> None:
    register(client)
    for state in ("open", "finalized"):
        response = client.get(f"/api/my-consultations?state={state}")
        assert response.status_code == 200
        assert response.json() == {"items": [], "next_cursor": None}


def test_private_read_headers_are_present(client) -> None:
    register(client)
    response = client.get("/api/my-consultations")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_open_list_exposes_only_allowlisted_fields(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    response = client.get("/api/my-consultations?state=open")
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == {"id", "state", "question", "audience", "published_at"}
    assert item["id"] == consultation_id
    assert item["state"] == "open"
    assert item["question"] == "Which one?"
    assert item["audience"] == "public"
    assert item["published_at"].endswith("Z")


def test_open_list_includes_public_and_private(client) -> None:
    register(client)
    pub_session, pub_images = publishable_session(client)
    publish(client, pub_session, pub_images, audience="public")
    priv_session, priv_images = publishable_session(client)
    publish(client, priv_session, priv_images, audience="private")

    response = client.get("/api/my-consultations?state=open")
    assert response.status_code == 200
    audiences = {item["audience"] for item in response.json()["items"]}
    assert audiences == {"public", "private"}


def test_finalized_list_exposes_exactly_minimum_fields(client, session_factory) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(
        client, session_id, image_ids, question="Sensitive?", context="secret"
    ).json()["id"]
    _set_state(session_factory, consultation_id, "finalized")

    response = client.get("/api/my-consultations?state=finalized")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert set(items[0]) == {"id", "state", "published_at"}
    assert items[0] == {
        "id": consultation_id,
        "state": "finalized",
        "published_at": items[0]["published_at"],
    }


@pytest.mark.parametrize("state", ["deleted", "removed"])
def test_terminal_rows_are_excluded_from_lists(client, session_factory, state) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    _set_state(session_factory, consultation_id, state)

    assert client.get("/api/my-consultations?state=open").json()["items"] == []
    assert client.get("/api/my-consultations?state=finalized").json()["items"] == []


def test_unpublished_upload_sessions_are_never_listed(client) -> None:
    register(client)
    create_session(client)

    assert client.get("/api/my-consultations?state=open").json()["items"] == []
    assert client.get("/api/my-consultations?state=finalized").json()["items"] == []


def test_cross_account_isolation_for_list_and_detail(client, session_factory) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    register(client, email="bob@example.com", alias="Bob")

    assert client.get("/api/my-consultations?state=open").json()["items"] == []
    detail = client.get(f"/api/my-consultations/{consultation_id}")
    assert detail.status_code == 404
    assert detail.json() == {"detail": {"code": "consultation_unavailable"}}


def test_private_token_holder_cannot_use_owner_read(client, session_factory) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]
    token = client.get(f"/api/consultations/{consultation_id}/private-link").json()["token"]

    register(client, email="bob@example.com", alias="Bob")

    detail = client.get(
        f"/api/my-consultations/{consultation_id}",
        headers={"X-NextPost-Private-Link": token},
    )
    assert detail.status_code == 404
    assert detail.json() == {"detail": {"code": "consultation_unavailable"}}


def test_owner_open_detail_exposes_full_stored_content(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(
        client, session_id, image_ids, question="Which photo?", context="For LinkedIn"
    ).json()["id"]

    response = client.get(f"/api/my-consultations/{consultation_id}")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "id",
        "state",
        "owner_nickname",
        "question",
        "context",
        "audience",
        "published_at",
        "photos",
    }
    assert body["state"] == "open"
    assert body["owner_nickname"] == "Ana"
    assert body["question"] == "Which photo?"
    assert body["context"] == "For LinkedIn"
    assert body["audience"] == "public"
    assert len(body["photos"]) == 2
    assert set(body["photos"][0]) == {"id", "width", "height"}


def test_owner_finalized_detail_returns_minimum_summary(client, session_factory) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, question="Q?", context="ctx").json()[
        "id"
    ]
    _set_state(session_factory, consultation_id, "finalized")

    response = client.get(f"/api/my-consultations/{consultation_id}")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "state", "published_at"}
    assert body["state"] == "finalized"


@pytest.mark.parametrize("state", ["deleted", "removed"])
def test_owner_terminal_detail_is_unavailable(client, session_factory, state) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    _set_state(session_factory, consultation_id, state)

    response = client.get(f"/api/my-consultations/{consultation_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


def test_owner_unknown_id_is_unavailable(client) -> None:
    register(client)
    response = client.get(f"/api/my-consultations/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


def test_disabled_private_link_owner_still_reads_detail(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]
    link = client.get(f"/api/consultations/{consultation_id}/private-link").json()
    disabled = client.post(
        f"/api/consultations/{consultation_id}/private-link/disable",
        json={"expected_generation": link["generation"]},
    )
    assert disabled.status_code == 200

    response = client.get(f"/api/my-consultations/{consultation_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "open"


def test_list_paginates_newest_first_with_stable_cursor(client, session_factory) -> None:
    register(client, email="ana@example.com", alias="Ana")
    with session_factory() as db:
        account_id = db.execute(
            select(Account.id).where(Account.email == "ana@example.com")
        ).scalar_one()
        base = datetime(2026, 1, 1, 12, 0, 0)
        for index in range(25):
            _insert_consultation(
                db, account_id, base + timedelta(minutes=index), question=f"Q{index}"
            )

    first = client.get("/api/my-consultations?state=open&limit=20")
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 20
    assert first_body["next_cursor"] is not None

    questions = [item["question"] for item in first_body["items"]]
    assert questions == [f"Q{index}" for index in range(24, 4, -1)]

    second = client.get(
        f"/api/my-consultations?state=open&limit=20&cursor={first_body['next_cursor']}"
    )
    assert second.status_code == 200
    second_body = second.json()
    assert [item["question"] for item in second_body["items"]] == [
        f"Q{index}" for index in range(4, -1, -1)
    ]
    assert second_body["next_cursor"] is None


def test_cursor_ties_do_not_duplicate_or_skip(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        published_at = datetime(2026, 1, 1, 12, 0, 0)
        ids = [_insert_consultation(db, account_id, published_at).id for _ in range(3)]

    collected: list[str] = []
    cursor = None
    while True:
        url = "/api/my-consultations?state=open&limit=1"
        if cursor is not None:
            url += f"&cursor={cursor}"
        response = client.get(url)
        body = response.json()
        collected.extend(item["id"] for item in body["items"])
        if body["next_cursor"] is None:
            break
        cursor = body["next_cursor"]

    assert len(collected) == len(set(collected)) == 3
    assert set(collected) == {str(i) for i in ids}


def test_cursor_and_filter_mismatch_is_rejected(client, session_factory) -> None:
    register(client)
    with session_factory() as db:
        account_id = db.execute(select(Account.id)).scalar_one()
        consultation = _insert_consultation(db, account_id, datetime(2026, 1, 1, 12, 0, 0))
        cursor = consultation_service.encode_cursor(
            "open", consultation.published_at, consultation.id
        )

    response = client.get(f"/api/my-consultations?state=finalized&cursor={cursor}")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_malformed_cursor_is_rejected(client) -> None:
    register(client)
    for cursor in ("not-base64!!!", "a" * 600, "%%%"):
        response = client.get(f"/api/my-consultations?state=open&cursor={cursor}")
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "validation_error"


def test_cursor_with_wrong_version_is_rejected(client) -> None:
    register(client)
    payload = (
        base64.urlsafe_b64encode(
            json.dumps(["v9", "open", "2026-01-01T12:00:00", str(uuid.uuid4())]).encode()
        )
        .decode()
        .rstrip("=")
    )
    response = client.get(f"/api/my-consultations?state=open&cursor={payload}")
    assert response.status_code == 422


@pytest.mark.parametrize("limit", [0, 51])
def test_limit_bounds_are_enforced(client, limit) -> None:
    register(client)
    response = client.get(f"/api/my-consultations?state=open&limit={limit}")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_invalid_state_filter_is_rejected(client) -> None:
    register(client)
    response = client.get("/api/my-consultations?state=unknown")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_finalized_owner_read_never_builds_open_projection(session_factory, monkeypatch) -> None:
    def boom(db, consultation):
        raise AssertionError("open projection must not run for finalized")

    monkeypatch.setattr(consultation_service, "_build_open_detail", boom)

    with session_factory() as db:
        account = _new_account(db)
        consultation = _insert_consultation(
            db, account.id, datetime(2026, 1, 1, 12, 0, 0), state="finalized"
        )

        result = consultation_service.read_my_consultation(db, consultation.id, account.id)

    assert result.state == "finalized"
    assert set(vars(result)) == {"id", "state", "published_at"}


def test_finalized_owner_read_checks_ownership_before_state(session_factory) -> None:
    with session_factory() as db:
        owner = _new_account(db, email="owner@example.com", alias="Owner")
        other = _new_account(db, email="other@example.com", alias="Other")
        consultation = _insert_consultation(
            db, owner.id, datetime(2026, 1, 1, 12, 0, 0), state="finalized"
        )

        with pytest.raises(consultation_service.ConsultationUnavailableError):
            consultation_service.read_my_consultation(db, consultation.id, other.id)


def test_finalized_owner_read_selects_only_minimal_columns(session_factory, monkeypatch) -> None:
    from sqlalchemy.orm import Session as OrmSession

    def no_full_row_get(self, entity, *args, **kwargs):
        raise AssertionError("db.get must not load a full row for a finalized owner read")

    monkeypatch.setattr(OrmSession, "get", no_full_row_get)

    with session_factory() as db:
        account = _new_account(db)
        consultation = _insert_consultation(
            db, account.id, datetime(2026, 1, 1, 12, 0, 0), state="finalized"
        )

        result = consultation_service.read_my_consultation(db, consultation.id, account.id)

    assert result.state == "finalized"
    assert set(vars(result)) == {"id", "state", "published_at"}
