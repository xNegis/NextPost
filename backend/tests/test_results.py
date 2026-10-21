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


def sign_in(client, email) -> None:
    response = client.post("/api/session", json={"email": email, "password": VALID_PASSWORD})
    assert response.status_code == 200


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


def _publish_public(client, *, count=2, question="Which one?"):
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client, count=count)
    response = publish(client, session_id, image_ids, question=question)
    assert response.status_code == 201
    consultation_id = response.json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    return consultation_id, photo_ids


def _publish_private(client):
    register(client, email="ana@example.com", alias="Ana")
    session_id, image_ids = publishable_session(client)
    response = publish(client, session_id, image_ids, audience="private")
    assert response.status_code == 201
    consultation_id = response.json()["id"]
    token = client.get(f"/api/consultations/{consultation_id}/private-link").json()["token"]
    detail = client.get(
        f"/api/consultations/{consultation_id}",
        headers={"X-NextPost-Private-Link": token},
    ).json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    return consultation_id, photo_ids, token


def _vote(client, consultation_id, photo_id, *, token=None):
    headers = {"X-NextPost-Private-Link": token} if token else None
    return client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_id},
        headers=headers,
    )


def test_results_require_authentication(client) -> None:
    response = client.get(f"/api/my-consultations/{uuid.uuid4()}/results")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_open_list_authentication_failure_has_private_headers(client) -> None:
    response = client.get("/api/my-consultations?state=open")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_owner_sees_zero_votes_for_every_option(client) -> None:
    consultation_id, photo_ids = _publish_public(client)

    response = client.get(f"/api/my-consultations/{consultation_id}/results")
    assert response.status_code == 200
    body = response.json()
    assert body["consultation_id"] == consultation_id
    assert body["state"] == "open"
    assert body["total_votes"] == 0
    assert [option["photo_id"] for option in body["options"]] == photo_ids
    assert [option["ordinal"] for option in body["options"]] == [0, 1]
    assert [option["vote_count"] for option in body["options"]] == [0, 0]
    assert response.headers["cache-control"] == "private, no-store"


def test_owner_sees_exact_counts_including_ties(client) -> None:
    consultation_id, photo_ids = _publish_public(client, count=3)

    register(client, email="bob@example.com", alias="Bob")
    assert _vote(client, consultation_id, photo_ids[0]).status_code == 201
    register(client, email="carol@example.com", alias="Carol")
    assert _vote(client, consultation_id, photo_ids[1]).status_code == 201
    register(client, email="dave@example.com", alias="Dave")
    assert _vote(client, consultation_id, photo_ids[2]).status_code == 201

    sign_in(client, "ana@example.com")
    body = client.get(f"/api/my-consultations/{consultation_id}/results").json()
    assert body["total_votes"] == 3
    assert [option["vote_count"] for option in body["options"]] == [1, 1, 1]
    assert [option["ordinal"] for option in body["options"]] == [0, 1, 2]


def test_uneven_counts_sum_to_total(client) -> None:
    consultation_id, photo_ids = _publish_public(client, count=2)

    register(client, email="bob@example.com", alias="Bob")
    assert _vote(client, consultation_id, photo_ids[0]).status_code == 201
    register(client, email="carol@example.com", alias="Carol")
    assert _vote(client, consultation_id, photo_ids[0]).status_code == 201
    register(client, email="dave@example.com", alias="Dave")
    assert _vote(client, consultation_id, photo_ids[1]).status_code == 201

    sign_in(client, "ana@example.com")
    body = client.get(f"/api/my-consultations/{consultation_id}/results").json()
    assert body["total_votes"] == 3
    counts = {option["photo_id"]: option["vote_count"] for option in body["options"]}
    assert counts[photo_ids[0]] == 2
    assert counts[photo_ids[1]] == 1


def test_results_support_ten_options_with_zero_votes(client) -> None:
    consultation_id, photo_ids = _publish_public(client, count=10)

    body = client.get(f"/api/my-consultations/{consultation_id}/results").json()
    assert body["total_votes"] == 0
    assert len(body["options"]) == 10
    assert [option["ordinal"] for option in body["options"]] == list(range(10))
    assert [option["vote_count"] for option in body["options"]] == [0] * 10


def test_results_do_not_expose_identity_or_forbidden_fields(client) -> None:
    consultation_id, photo_ids = _publish_public(client)
    register(client, email="bob@example.com", alias="Bob")
    _vote(client, consultation_id, photo_ids[0])
    sign_in(client, "ana@example.com")

    body = client.get(f"/api/my-consultations/{consultation_id}/results").json()
    assert set(body) == {"consultation_id", "state", "total_votes", "options"}
    assert set(body["options"][0]) == {"photo_id", "ordinal", "vote_count"}
    for option in body["options"]:
        assert set(option) == {"photo_id", "ordinal", "vote_count"}


def test_private_results_are_owner_authority_not_link_authority(client) -> None:
    consultation_id, photo_ids, _token = _publish_private(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.get(
        f"/api/my-consultations/{consultation_id}/results",
        headers={"X-NextPost-Private-Link": _token},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}

    sign_in(client, "ana@example.com")
    body = client.get(f"/api/my-consultations/{consultation_id}/results").json()
    assert body["total_votes"] == 0
    assert len(body["options"]) == 2


def test_unknown_consultation_is_unavailable(client) -> None:
    register(client)
    response = client.get(f"/api/my-consultations/{uuid.uuid4()}/results")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


def test_another_owner_cannot_read_results(client) -> None:
    consultation_id, _photo_ids = _publish_public(client)
    register(client, email="bob@example.com", alias="Bob")
    response = client.get(f"/api/my-consultations/{consultation_id}/results")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_terminal_consultation_results_are_unavailable(client, session_factory, state) -> None:
    from app.models import Consultation, ConsultationState

    consultation_id, _photo_ids = _publish_public(client)
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()

    response = client.get(f"/api/my-consultations/{consultation_id}/results")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


def test_open_list_rows_include_current_total_votes(client) -> None:
    consultation_id, photo_ids = _publish_public(client)

    register(client, email="bob@example.com", alias="Bob")
    assert _vote(client, consultation_id, photo_ids[0]).status_code == 201
    register(client, email="carol@example.com", alias="Carol")
    assert _vote(client, consultation_id, photo_ids[0]).status_code == 201

    sign_in(client, "ana@example.com")
    body = client.get("/api/my-consultations?state=open").json()
    assert body["items"][0]["total_votes"] == 2


def test_finalized_list_rows_remain_minimal(client, session_factory) -> None:
    from app.models import Consultation, ConsultationState

    consultation_id, _photo_ids = _publish_public(client)
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        consultation.state = ConsultationState.finalized
        db.commit()

    body = client.get("/api/my-consultations?state=finalized").json()
    assert set(body["items"][0]) == {"id", "state", "published_at", "result"}
    assert body["items"][0]["result"] is None
