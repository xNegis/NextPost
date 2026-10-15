import io
import uuid

import pytest
from PIL import Image

from app.config import get_settings

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


def sign_in(client, email="ana@example.com") -> None:
    response = client.post("/api/session", json={"email": email, "password": VALID_PASSWORD})
    assert response.status_code == 200


def create_session(client) -> str:
    response = client.post("/api/photo-upload-sessions")
    assert response.status_code == 201
    return response.json()["id"]


def upload(
    client,
    session_id: str,
    content: bytes | None = None,
    attempt_id: str | None = None,
    filename: str = "photo.jpg",
):
    payload = content if content is not None else _jpeg_bytes()
    return client.post(
        f"/api/photo-upload-sessions/{session_id}/images",
        files={"file": (filename, payload, "image/jpeg")},
        data={"attempt_id": attempt_id or str(uuid.uuid4())},
    )


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in (
        "CONSULTATION_MIN_PHOTOS",
        "CONSULTATION_MAX_PHOTOS",
        "PHOTO_MAX_INPUT_BYTES",
        "PHOTO_MAX_PIXELS",
        "PHOTO_MAX_OUTPUT_EDGE",
        "CONSULTATION_QUESTION_MAX_LENGTH",
        "CONSULTATION_CONTEXT_MAX_LENGTH",
    ):
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_config_requires_authentication(client) -> None:
    assert client.get("/api/application-config").status_code == 401


def test_config_returns_exact_non_secret_values(client) -> None:
    register(client)
    response = client.get("/api/application-config")

    assert response.status_code == 200
    assert response.json() == {
        "consultation_min_photos": 2,
        "consultation_max_photos": 10,
        "max_open_consultations": 3,
        "photo_max_input_bytes": 15728640,
        "consultation_question_max_length": 120,
        "consultation_context_max_length": 500,
    }


def test_config_returns_effective_text_limits(client, monkeypatch) -> None:
    register(client)
    monkeypatch.setenv("CONSULTATION_QUESTION_MAX_LENGTH", "60")
    monkeypatch.setenv("CONSULTATION_CONTEXT_MAX_LENGTH", "200")
    get_settings.cache_clear()

    response = client.get("/api/application-config")

    assert response.status_code == 200
    body = response.json()
    assert body["consultation_question_max_length"] == 60
    assert body["consultation_context_max_length"] == 200


def test_photo_endpoints_require_authentication(client) -> None:
    assert client.post("/api/photo-upload-sessions").status_code == 401
    session_id = str(uuid.uuid4())
    image_id = str(uuid.uuid4())
    assert client.post(f"/api/photo-upload-sessions/{session_id}/lease").status_code == 401
    assert (
        client.get(f"/api/photo-upload-sessions/{session_id}/images/{image_id}/content").status_code
        == 401
    )


def test_create_and_renew_session(client) -> None:
    register(client)
    session_id = create_session(client)

    response = client.post(f"/api/photo-upload-sessions/{session_id}/lease")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == session_id
    assert body["lease_expires_at"].endswith("Z")


def test_upload_returns_normalized_metadata_and_content(client) -> None:
    register(client)
    session_id = create_session(client)

    response = upload(client, session_id)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "width", "height"}
    assert body["width"] == 64
    assert body["height"] == 64

    content = client.get(f"/api/photo-upload-sessions/{session_id}/images/{body['id']}/content")
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/jpeg"
    assert content.headers["cache-control"] == "private, no-store"
    assert content.headers["x-content-type-options"] == "nosniff"
    assert content.content.startswith(b"\xff\xd8")


def test_upload_sniffs_content_not_filename(client) -> None:
    register(client)
    session_id = create_session(client)

    response = upload(client, session_id, filename="totally.a.webp", content=_jpeg_bytes())

    assert response.status_code == 201


def test_non_owner_cannot_read(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    session_id = create_session(client)
    image_id = upload(client, session_id).json()["id"]

    register(client, email="bob@example.com", alias="Bob")

    content = client.get(f"/api/photo-upload-sessions/{session_id}/images/{image_id}/content")
    assert content.status_code == 404
    assert content.json() == {"detail": {"code": "not_found"}}


def test_unknown_session_is_not_found(client) -> None:
    register(client)
    response = upload(client, str(uuid.uuid4()))
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "not_found"}}


def test_discard_revokes_session_and_images(client) -> None:
    register(client)
    session_id = create_session(client)
    image_id = upload(client, session_id).json()["id"]

    assert client.delete(f"/api/photo-upload-sessions/{session_id}").status_code == 204

    content = client.get(f"/api/photo-upload-sessions/{session_id}/images/{image_id}/content")
    assert content.status_code == 409
    assert content.json() == {"detail": {"code": "session_inactive"}}


def test_remove_image_is_idempotent_and_revokes(client) -> None:
    register(client)
    session_id = create_session(client)
    image_id = upload(client, session_id).json()["id"]

    assert (
        client.delete(f"/api/photo-upload-sessions/{session_id}/images/{image_id}").status_code
        == 204
    )
    assert (
        client.delete(f"/api/photo-upload-sessions/{session_id}/images/{image_id}").status_code
        == 204
    )
    content = client.get(f"/api/photo-upload-sessions/{session_id}/images/{image_id}/content")
    assert content.status_code == 404


def test_same_attempt_replay_is_idempotent(client) -> None:
    register(client)
    session_id = create_session(client)
    attempt_id = str(uuid.uuid4())

    first = upload(client, session_id, attempt_id=attempt_id)
    second = upload(client, session_id, attempt_id=attempt_id)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_invalid_attempt_id_is_rejected(client) -> None:
    register(client)
    session_id = create_session(client)

    response = upload(client, session_id, attempt_id="not-a-uuid")

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "invalid_attempt"}}


def test_unsupported_format_is_rejected(client) -> None:
    register(client)
    session_id = create_session(client)

    response = upload(client, session_id, content=b"not an image at all")

    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "invalid_image"}}


def test_input_too_large_is_rejected(client, monkeypatch) -> None:
    register(client)
    session_id = create_session(client)
    monkeypatch.setenv("PHOTO_MAX_INPUT_BYTES", "64")
    get_settings.cache_clear()

    response = upload(client, session_id)

    assert response.status_code == 413
    assert response.json() == {"detail": {"code": "input_too_large"}}


def test_photo_limit_is_enforced(client, monkeypatch) -> None:
    register(client)
    session_id = create_session(client)
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "5")
    get_settings.cache_clear()

    for _ in range(5):
        assert upload(client, session_id).status_code == 201
    sixth = upload(client, session_id)

    assert sixth.status_code == 409
    assert sixth.json() == {"detail": {"code": "photo_limit_reached"}}


def test_discard_is_idempotent_for_owner(client) -> None:
    register(client)
    session_id = create_session(client)

    assert client.delete(f"/api/photo-upload-sessions/{session_id}").status_code == 204
    assert client.delete(f"/api/photo-upload-sessions/{session_id}").status_code == 204
