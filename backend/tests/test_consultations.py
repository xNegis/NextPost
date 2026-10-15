import io
import uuid

import pytest
from PIL import Image

from app.config import get_settings
from app.models import Consultation, ConsultationState

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


def test_consultation_endpoints_require_authentication(client) -> None:
    assert client.get("/api/consultation-capacity").status_code == 401
    consultation_id = str(uuid.uuid4())
    assert client.get(f"/api/consultations/{consultation_id}").status_code == 401
    assert (
        client.get(
            f"/api/consultations/{consultation_id}/photos/{uuid.uuid4()}/content"
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/consultations",
            json={
                "session_id": str(uuid.uuid4()),
                "ordered_image_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
                "question": "Which one?",
                "audience": "public",
            },
        ).status_code
        == 401
    )


def test_publish_public_consultation(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = publish(client, session_id, image_ids)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "state", "audience"}
    assert body["state"] == "open"
    assert body["audience"] == "public"


def test_publish_private_creates_generation_one_link(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = publish(client, session_id, image_ids, audience="private")

    assert response.status_code == 201
    consultation_id = response.json()["id"]

    link = client.get(f"/api/consultations/{consultation_id}/private-link")
    assert link.status_code == 200
    body = link.json()
    assert body["active"] is True
    assert body["generation"] == "1"
    assert body["token"].startswith("v1.")


def test_publish_rejects_missing_audience(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": "Which one?",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"
    assert response.json()["detail"]["field_errors"]["audience"] == "Choose an audience."


def test_publish_rejects_empty_question(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = publish(client, session_id, image_ids, question="   ")

    assert response.status_code == 422
    assert response.json()["detail"]["field_errors"]["question"] == "Enter a question."


def test_publish_rejects_wrong_owner_session(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)

    register(client, email="bob@example.com", alias="Bob")

    response = publish(client, session_id, image_ids)

    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "not_found"}}


def test_publish_rejects_non_ready_missing_count(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client, count=1)

    response = publish(client, session_id, image_ids)

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "publication_invalid"}}


def test_duplicate_publish_returns_same_consultation(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    first = publish(client, session_id, image_ids, question="Which one?")
    second = publish(client, session_id, image_ids, question="Which one?")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_changed_payload_for_consumed_session_conflicts(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    first = publish(client, session_id, image_ids, question="Which one?")
    assert first.status_code == 201

    changed = publish(client, session_id, image_ids, question="A different question?")

    assert changed.status_code == 409
    assert changed.json() == {"detail": {"code": "consultation_conflict"}}


def test_open_cap_is_enforced(client, monkeypatch) -> None:
    monkeypatch.setenv("MAX_OPEN_CONSULTATIONS", "1")
    get_settings.cache_clear()
    register(client)

    first_session, first_images = publishable_session(client)
    assert publish(client, first_session, first_images).status_code == 201

    second_session, second_images = publishable_session(client)
    capped = publish(client, second_session, second_images)

    assert capped.status_code == 409
    assert capped.json() == {"detail": {"code": "max_open_consultations_reached"}}


def test_capacity_reflects_open_count(client) -> None:
    register(client)
    capacity = client.get("/api/consultation-capacity")
    assert capacity.status_code == 200
    assert capacity.json() == {"open_count": 0, "limit": 3, "can_start": True}

    session_id, image_ids = publishable_session(client)
    publish(client, session_id, image_ids)

    capacity = client.get("/api/consultation-capacity")
    assert capacity.json() == {"open_count": 1, "limit": 3, "can_start": True}


def test_detail_public_visible_to_other_registered_account(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    register(client, email="bob@example.com", alias="Bob")

    response = client.get(f"/api/consultations/{consultation_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == consultation_id
    assert body["owner_nickname"] == "Ana"
    assert body["question"] == "Which one?"
    assert body["audience"] == "public"
    assert len(body["photos"]) == 2


def test_detail_private_requires_current_link(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]
    link = client.get(f"/api/consultations/{consultation_id}/private-link").json()
    token = link["token"]

    register(client, email="bob@example.com", alias="Bob")

    denied = client.get(f"/api/consultations/{consultation_id}")
    assert denied.status_code == 404
    assert denied.json() == {"detail": {"code": "consultation_unavailable"}}

    allowed = client.get(
        f"/api/consultations/{consultation_id}", headers={"X-NextPost-Private-Link": token}
    )
    assert allowed.status_code == 200


def test_owner_can_read_private_without_token(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]

    response = client.get(f"/api/consultations/{consultation_id}")
    assert response.status_code == 200


def test_photo_content_headers_and_access(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_id = detail["photos"][0]["id"]

    register(client, email="bob@example.com", alias="Bob")
    content = client.get(f"/api/consultations/{consultation_id}/photos/{photo_id}/content")

    assert content.status_code == 200
    assert content.headers["content-type"] == "image/jpeg"
    assert content.headers["cache-control"] == "private, no-store"
    assert content.headers["x-content-type-options"] == "nosniff"
    assert content.headers["referrer-policy"] == "no-referrer"
    assert content.content.startswith(b"\xff\xd8")


def test_photo_content_cross_consultation_is_denied(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    photo_id = client.get(f"/api/consultations/{consultation_id}").json()["photos"][0]["id"]

    other_session, other_images = publishable_session(client)
    other_consultation_id = publish(client, other_session, other_images).json()["id"]

    content = client.get(f"/api/consultations/{other_consultation_id}/photos/{photo_id}/content")
    assert content.status_code == 404
    assert content.json() == {"detail": {"code": "consultation_unavailable"}}


def test_consumed_session_temporary_read_is_rejected(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    publish(client, session_id, image_ids)

    content = client.get(f"/api/photo-upload-sessions/{session_id}/images/{image_ids[0]}/content")
    assert content.status_code == 409
    assert content.json() == {"detail": {"code": "session_inactive"}}


def test_consumed_session_remove_is_rejected(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    publish(client, session_id, image_ids)

    removed = client.delete(f"/api/photo-upload-sessions/{session_id}/images/{image_ids[0]}")
    assert removed.status_code == 409
    assert removed.json() == {"detail": {"code": "session_inactive"}}


def test_link_disable_replace_create_flow(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]

    initial = client.get(f"/api/consultations/{consultation_id}/private-link").json()
    token = initial["token"]

    disabled = client.post(
        f"/api/consultations/{consultation_id}/private-link/disable",
        json={"expected_generation": initial["generation"]},
    )
    assert disabled.status_code == 200
    assert disabled.json() == {"active": False, "generation": "1", "token": None}

    created = client.post(
        f"/api/consultations/{consultation_id}/private-link/create",
        json={"expected_generation": "1"},
    )
    assert created.status_code == 200
    assert created.json()["active"] is True
    assert created.json()["generation"] == "2"
    new_token = created.json()["token"]

    assert new_token != token

    # Old token no longer grants access.
    register(client, email="bob@example.com", alias="Bob")
    old = client.get(
        f"/api/consultations/{consultation_id}", headers={"X-NextPost-Private-Link": token}
    )
    assert old.status_code == 404
    fresh = client.get(
        f"/api/consultations/{consultation_id}", headers={"X-NextPost-Private-Link": new_token}
    )
    assert fresh.status_code == 200


def test_link_stale_generation_conflicts(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]

    stale = client.post(
        f"/api/consultations/{consultation_id}/private-link/disable",
        json={"expected_generation": "99"},
    )
    assert stale.status_code == 409
    assert stale.json() == {"detail": {"code": "link_conflict"}}


def test_public_consultation_cannot_mint_link(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]

    response = client.get(f"/api/consultations/{consultation_id}/private-link")
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "not_private"}}


def test_hostile_origin_is_rejected(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": "Which one?",
            "audience": "public",
        },
        headers={"Origin": "https://evil.example.com"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": {"code": "origin_not_allowed"}}


def test_null_origin_is_rejected(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": "Which one?",
            "audience": "public",
        },
        headers={"Origin": "null"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": {"code": "origin_not_allowed"}}


def test_trusted_origin_is_allowed(client) -> None:
    register(client)
    session_id, image_ids = publishable_session(client)

    response = client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": "Which one?",
            "audience": "public",
        },
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 201


def _set_terminal_state(session_factory, consultation_id: str, state: str) -> None:
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_terminal_state_hides_detail_photos_and_link(client, session_factory, state) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids, audience="private").json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    link = client.get(f"/api/consultations/{consultation_id}/private-link").json()
    token = link["token"]

    _set_terminal_state(session_factory, consultation_id, state)

    # A still-current Private token cannot override the terminal lifecycle.
    detail_response = client.get(
        f"/api/consultations/{consultation_id}",
        headers={"X-NextPost-Private-Link": token},
    )
    assert detail_response.status_code == 404
    assert detail_response.json() == {"detail": {"code": "consultation_unavailable"}}

    for photo_id in photo_ids:
        content = client.get(
            f"/api/consultations/{consultation_id}/photos/{photo_id}/content",
            headers={"X-NextPost-Private-Link": token},
        )
        assert content.status_code == 404
        assert content.json() == {"detail": {"code": "consultation_unavailable"}}

    assert client.get(f"/api/consultations/{consultation_id}/private-link").status_code == 404

    for operation in ("disable", "replace", "create"):
        mutation = client.post(
            f"/api/consultations/{consultation_id}/private-link/{operation}",
            json={"expected_generation": link["generation"]},
        )
        assert mutation.status_code == 404
        assert mutation.json() == {"detail": {"code": "consultation_unavailable"}}


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_terminal_state_denies_other_registered_account(client, session_factory, state) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    consultation_id = publish(client, session_id, image_ids).json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]

    _set_terminal_state(session_factory, consultation_id, state)

    register(client, email="bob@example.com", alias="Bob")

    assert client.get(f"/api/consultations/{consultation_id}").status_code == 404
    for photo_id in photo_ids:
        content = client.get(f"/api/consultations/{consultation_id}/photos/{photo_id}/content")
        assert content.status_code == 404
        assert content.json() == {"detail": {"code": "consultation_unavailable"}}
