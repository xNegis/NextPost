import io
import uuid

import pytest
from PIL import Image
from sqlalchemy import select

from app.config import get_settings
from app.models import (
    Consultation,
    ConsultationState,
    Vote,
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


def _publish_public_consultation(client) -> tuple[str, list[str]]:
    session_id, image_ids = publishable_session(client)
    response = publish(client, session_id, image_ids)
    assert response.status_code == 201
    consultation_id = response.json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    return consultation_id, photo_ids


def _publish_private_consultation(client) -> tuple[str, list[str], str]:
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


def test_my_vote_requires_authentication(client) -> None:
    response = client.get(f"/api/consultations/{uuid.uuid4()}/my-vote")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_votes_require_authentication(client) -> None:
    response = client.post(
        f"/api/consultations/{uuid.uuid4()}/votes",
        json={"photo_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401


def test_my_vote_returns_not_voted_for_eligible_non_owner(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, _ = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.get(f"/api/consultations/{consultation_id}/my-vote")
    assert response.status_code == 200
    assert response.json() == {"status": "not_voted"}
    assert response.headers["cache-control"] == "private, no-store"


def test_cast_vote_then_read_back(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_ids[0]},
    )
    assert response.status_code == 201
    assert response.json() == {"status": "voted", "photo_id": photo_ids[0]}

    read = client.get(f"/api/consultations/{consultation_id}/my-vote")
    assert read.status_code == 200
    assert read.json() == {"status": "voted", "photo_id": photo_ids[0]}


def test_exact_replay_returns_existing_vote_with_200(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/votes"
    assert client.post(url, json={"photo_id": photo_ids[0]}).status_code == 201
    replay = client.post(url, json={"photo_id": photo_ids[0]})
    assert replay.status_code == 200
    assert replay.json() == {"status": "voted", "photo_id": photo_ids[0]}


def test_different_option_is_conflict_and_not_overwritten(client, session_factory) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/votes"
    assert client.post(url, json={"photo_id": photo_ids[0]}).status_code == 201

    conflict = client.post(url, json={"photo_id": photo_ids[1]})
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": {"code": "vote_already_recorded"}}

    assert client.get(f"/api/consultations/{consultation_id}/my-vote").json() == {
        "status": "voted",
        "photo_id": photo_ids[0],
    }

    with session_factory() as db:
        votes = db.execute(select(Vote)).scalars().all()
    assert len(votes) == 1
    assert votes[0].consultation_photo_id == uuid.UUID(photo_ids[0])


def test_owner_cannot_vote_or_read_own_vote(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    response = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_ids[0]},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}

    read = client.get(f"/api/consultations/{consultation_id}/my-vote")
    assert read.status_code == 404


def test_cross_consultation_option_is_invalid_selection(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    first_id, _ = _publish_public_consultation(client)
    _, other_photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.post(
        f"/api/consultations/{first_id}/votes",
        json={"photo_id": other_photo_ids[0]},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "invalid_selection"}}


def test_unknown_photo_is_invalid_selection(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, _ = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": {"code": "invalid_selection"}}


def test_unknown_consultation_is_unavailable(client) -> None:
    register(client)
    response = client.get(f"/api/consultations/{uuid.uuid4()}/my-vote")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"photo_id": "not-a-uuid"},
        {"photo_id": str(uuid.uuid4()), "extra": True},
        {"photo": str(uuid.uuid4())},
    ],
)
def test_malformed_vote_payload_is_422(client, body) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, _ = _publish_public_consultation(client)
    register(client, email="bob@example.com", alias="Bob")

    response = client.post(f"/api/consultations/{consultation_id}/votes", json=body)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


@pytest.mark.parametrize("state", ["finalized", "deleted", "removed"])
def test_terminal_consultation_rejects_vote_and_read(client, session_factory, state) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        assert consultation is not None
        consultation.state = ConsultationState(state)
        db.commit()

    register(client, email="bob@example.com", alias="Bob")
    post = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_ids[0]},
    )
    assert post.status_code == 404
    assert client.get(f"/api/consultations/{consultation_id}/my-vote").status_code == 404

    with session_factory() as db:
        assert db.execute(select(Vote)).scalars().all() == []


def test_private_consultation_requires_current_token_for_vote(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids, token = _publish_private_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/votes"
    headers = {"X-NextPost-Private-Link": token}

    assert client.post(url, json={"photo_id": photo_ids[0]}).status_code == 404
    assert (
        client.post(
            url, json={"photo_id": photo_ids[0]}, headers={"X-NextPost-Private-Link": "v1.aaaa"}
        ).status_code
        == 404
    )

    success = client.post(url, json={"photo_id": photo_ids[0]}, headers=headers)
    assert success.status_code == 201
    assert success.json() == {"status": "voted", "photo_id": photo_ids[0]}

    read = client.get(f"/api/consultations/{consultation_id}/my-vote", headers=headers)
    assert read.json() == {"status": "voted", "photo_id": photo_ids[0]}


def test_replaced_private_token_no_longer_votes(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids, token = _publish_private_consultation(client)
    replaced = client.post(
        f"/api/consultations/{consultation_id}/private-link/replace",
        json={"expected_generation": "1"},
    ).json()["token"]

    register(client, email="bob@example.com", alias="Bob")
    url = f"/api/consultations/{consultation_id}/votes"
    assert (
        client.post(
            url,
            json={"photo_id": photo_ids[0]},
            headers={"X-NextPost-Private-Link": token},
        ).status_code
        == 404
    )
    success = client.post(
        url,
        json={"photo_id": photo_ids[0]},
        headers={"X-NextPost-Private-Link": replaced},
    )
    assert success.status_code == 201


def test_vote_post_rejects_untrusted_origin(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    response = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_ids[0]},
        headers={"Origin": "https://evil.example.com"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": {"code": "origin_not_allowed"}}


def test_feed_marks_has_voted_for_current_account_only(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish_public_consultation(client)

    register(client, email="bob@example.com", alias="Bob")
    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["has_voted"] is False

    client.post(f"/api/consultations/{consultation_id}/votes", json={"photo_id": photo_ids[0]})
    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["has_voted"] is True

    register(client, email="carol@example.com", alias="Carol")
    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["has_voted"] is False
    assert item["is_owner"] is False


def test_feed_owner_card_never_has_voted(client) -> None:
    register(client, email="ana@example.com", alias="Ana")
    _publish_public_consultation(client)

    item = client.get("/api/consultations/feed").json()["items"][0]
    assert item["is_owner"] is True
    assert item["has_voted"] is False
