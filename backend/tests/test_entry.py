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


def _publish_public_consultation(client) -> str:
    session_id, image_ids = _publishable_session(client)
    response = publish(client, session_id, image_ids)
    assert response.status_code == 201
    return response.json()["id"]


def _publish_private_consultation(client) -> tuple[str, str]:
    session_id, image_ids = _publishable_session(client)
    response = publish(client, session_id, image_ids, audience="private")
    assert response.status_code == 201
    consultation_id = response.json()["id"]
    token = client.get(f"/api/consultations/{consultation_id}/private-link").json()["token"]
    return consultation_id, token


def _publishable_session(client, count: int = 2) -> tuple[str, list[str]]:
    session_id = create_session(client)
    image_ids = [upload(client, session_id) for _ in range(count)]
    return session_id, image_ids


def _assert_private_headers(response) -> None:
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_entry_requires_authentication(client) -> None:
    response = client.get(f"/api/consultations/{uuid.uuid4()}/entry")
    assert response.status_code == 401
    _assert_private_headers(response)


def test_entry_unknown_consultation_is_unavailable(client) -> None:
    register(client)
    response = client.get(f"/api/consultations/{uuid.uuid4()}/entry")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}
    _assert_private_headers(response)


def test_entry_public_owner_returns_owner(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id = _publish_public_consultation(client)

    response = client.get(f"/api/consultations/{consultation_id}/entry")
    assert response.status_code == 200
    assert response.json() == {"role": "owner"}
    _assert_private_headers(response)


def test_entry_public_non_owner_returns_reader(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.get(f"/api/consultations/{consultation_id}/entry")
    assert response.status_code == 200
    assert response.json() == {"role": "reader"}
    _assert_private_headers(response)


def test_entry_private_owner_returns_owner_without_token(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, _ = _publish_private_consultation(client)

    response = client.get(f"/api/consultations/{consultation_id}/entry")
    assert response.status_code == 200
    assert response.json() == {"role": "owner"}


def test_entry_private_non_owner_requires_current_token(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, token = _publish_private_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/entry"

    assert client.get(url).status_code == 404
    assert client.get(url, headers={"X-NextPost-Private-Link": "v1.aaaa"}).status_code == 404

    response = client.get(url, headers={"X-NextPost-Private-Link": token})
    assert response.status_code == 200
    assert response.json() == {"role": "reader"}


def test_entry_replaced_private_token_is_unavailable(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, token = _publish_private_consultation(client)
    replaced = client.post(
        f"/api/consultations/{consultation_id}/private-link/replace",
        json={"expected_generation": "1"},
    ).json()["token"]

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/entry"
    assert client.get(url, headers={"X-NextPost-Private-Link": token}).status_code == 404
    assert client.get(url, headers={"X-NextPost-Private-Link": replaced}).status_code == 200


def test_entry_disabled_private_token_is_unavailable(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, token = _publish_private_consultation(client)
    client.post(
        f"/api/consultations/{consultation_id}/private-link/disable",
        json={"expected_generation": "1"},
    )

    register(client, email="bob@example.com", alias="Bob")
    response = client.get(
        f"/api/consultations/{consultation_id}/entry",
        headers={"X-NextPost-Private-Link": token},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_entry_terminal_consultation_is_unavailable(client, session_factory, state) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id = _publish_public_consultation(client)
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()

    register(client, email="bob@example.com", alias="Bob")
    response = client.get(f"/api/consultations/{consultation_id}/entry")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


def test_entry_returns_exactly_one_field(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id = _publish_public_consultation(client)
    register(client, email="bob@example.com", alias="Bob")

    response = client.get(f"/api/consultations/{consultation_id}/entry")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["role"]
