import io
import logging
import uuid
from datetime import datetime, timezone

import pytest
from PIL import Image
from sqlalchemy import select

from app.consultation_deletion_service import delete_consultation
from app.consultation_service import (
    ConsultationConflictError,
    ConsultationUnavailableError,
    list_my_consultations,
    read_my_consultation,
)
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
    Vote,
)

T0 = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)

VALID_PASSWORD = "correct-horse-battery-staple"


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (200, 30, 30)).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _account(db, email="owner@example.com", alias="Owner") -> Account:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"{email.split('@')[0]}{suffix}@{email.split('@')[1]}",
        alias=f"{alias}{suffix}",
        alias_canonical=f"{alias}{suffix}".lower(),
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account


def _seed_consultation(
    db, account_id, *, audience="public", state="open", with_votes=0, storage=None
) -> tuple[Consultation, list[PhotoUploadImage], list[ConsultationPhoto], PhotoUploadSession]:
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=T0,
    )
    db.add(session)
    db.flush()

    images: list[PhotoUploadImage] = []
    for _ in range(2):
        key = uuid.uuid4().hex
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=key,
            width=10,
            height=10,
        )
        db.add(image)
        db.flush()
        if storage is not None:
            storage.write_normalized(key, b"x")
        images.append(image)

    consultation = Consultation(
        owner_id=account_id,
        question="Which one?",
        context="For LinkedIn",
        audience=audience,
        state=ConsultationState(state),
        published_at=T0,
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
        private_link_generation=1 if audience == "private" else 0,
        private_link_active=(audience == "private"),
    )
    db.add(consultation)
    db.flush()

    photos: list[ConsultationPhoto] = []
    for ordinal, image in enumerate(images):
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo)

    for index in range(with_votes):
        voter = Account(
            email=f"voter{index}{uuid.uuid4().hex[:8]}@example.com",
            alias=f"Voter{index}",
            alias_canonical=f"voter{index}".lower(),
            password_hash="x",
        )
        db.add(voter)
        db.flush()
        db.add(
            Vote(
                consultation_id=consultation.id,
                voter_id=voter.id,
                consultation_photo_id=photos[0].id,
            )
        )

    db.commit()
    return consultation, images, photos, session


def test_open_deletion_marks_media_removes_votes_and_terminalizes(session_factory, storage) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, images, photos, _ = _seed_consultation(
            db, account.id, with_votes=2, storage=storage
        )
        cid = consultation.id
        image_ids = [image.id for image in images]

        outcome = delete_consultation(db, cid, account.id, "open", now=T0)

        assert outcome.classification == "first"
        assert outcome.votes_removed == 2
        assert outcome.images_marked == 2

        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.deleted
        assert row.author_deleted_at is not None
        assert row.question is None
        assert row.context is None
        assert row.audience is None
        assert row.fingerprint is None
        assert int(row.private_link_generation) == 0
        assert row.private_link_active is False

    with session_factory() as db:
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None
        for image_id in image_ids:
            image = db.get(PhotoUploadImage, image_id)
            assert image is not None
            assert image.state == PhotoImageState.revoked
            assert image.deletion_requested_at is not None


def test_finalized_withdrawal_preserves_lifecycle_and_sanitizes(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized", with_votes=1)
        cid = consultation.id

        outcome = delete_consultation(db, cid, account.id, "finalized", now=T0)

        assert outcome.classification == "first"
        assert outcome.votes_removed == 1
        assert outcome.images_marked == 0

        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        assert row.author_deleted_at is not None
        assert row.question is None
        assert row.audience is None
        assert int(row.private_link_generation) == 0
        assert row.private_link_active is False

    with session_factory() as db:
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None


def test_open_exact_replay_is_idempotent(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, with_votes=1)
        cid = consultation.id

        first = delete_consultation(db, cid, account.id, "open", now=T0)
        replay = delete_consultation(db, cid, account.id, "open", now=T0)

        assert first.classification == "first"
        assert replay.classification == "replay"
        assert replay.votes_removed == 0

    with session_factory() as db:
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.deleted
        assert row.author_deleted_at is not None


def test_finalized_exact_replay_is_idempotent(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized")
        cid = consultation.id

        delete_consultation(db, cid, account.id, "finalized", now=T0)
        replay = delete_consultation(db, cid, account.id, "finalized", now=T0)

        assert replay.classification == "replay"


def test_stale_open_request_against_finalized_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized")
        cid = consultation.id

        with pytest.raises(ConsultationConflictError):
            delete_consultation(db, cid, account.id, "open", now=T0)

        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        assert row.author_deleted_at is None


def test_finalized_request_against_open_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="open")
        cid = consultation.id

        with pytest.raises(ConsultationConflictError):
            delete_consultation(db, cid, account.id, "finalized", now=T0)


def test_deleted_row_without_marker_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="deleted")
        cid = consultation.id

        with pytest.raises(ConsultationConflictError):
            delete_consultation(db, cid, account.id, "open", now=T0)


def test_foreign_consultation_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        other = _account(db, email="other@example.com", alias="Other")
        consultation, _, _, _ = _seed_consultation(db, owner.id)

        with pytest.raises(ConsultationUnavailableError):
            delete_consultation(db, consultation.id, other.id, "open", now=T0)


def test_unknown_consultation_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        with pytest.raises(ConsultationUnavailableError):
            delete_consultation(db, uuid.uuid4(), account.id, "open", now=T0)


def test_removed_consultation_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="removed")

        with pytest.raises(ConsultationUnavailableError):
            delete_consultation(db, consultation.id, account.id, "open", now=T0)


def test_open_deletion_rolls_back_on_marker_failure(session_factory, monkeypatch) -> None:
    def boom(db, consultation, now=None):
        raise RuntimeError("marker failure")

    monkeypatch.setattr("app.consultation_deletion_service.mark_media_for_erasure", boom)

    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, with_votes=1)
        cid = consultation.id

        with pytest.raises(RuntimeError):
            delete_consultation(db, cid, account.id, "open", now=T0)

        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.open
        assert row.author_deleted_at is None
        assert row.question == "Which one?"
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is not None


def test_open_deletion_converges_through_rf37_reconciliation(session_factory, storage) -> None:
    from app.photo_erasure_service import reconcile_terminal_media

    with session_factory() as db:
        account = _account(db)
        consultation, images, _, source_session = _seed_consultation(
            db, account.id, storage=storage
        )
        cid = consultation.id
        keys = [image.storage_key for image in images]

        delete_consultation(db, cid, account.id, "open", now=T0)

        report = reconcile_terminal_media(db, storage, now=T0)

        assert report.sessions_completed == 1
        assert report.objects_deleted == 2
        assert report.objects_failed == 0

    with session_factory() as db:
        for key in keys:
            assert storage.exists(key) is False
        row = db.get(Consultation, cid)
        assert row.source_session_id is None
        assert db.get(PhotoUploadSession, source_session.id) is None


def test_withdrawn_finalized_is_excluded_from_list_and_detail(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized")
        cid = consultation.id

        delete_consultation(db, cid, account.id, "finalized", now=T0)

        result = list_my_consultations(db, account.id, "finalized", 20, None)
        assert result.items == []

        with pytest.raises(ConsultationUnavailableError):
            read_my_consultation(db, cid, account.id)


# --- API tests ---------------------------------------------------------------------------


def _register(client, email="ana@example.com", alias="Ana") -> None:
    response = client.post(
        "/api/accounts",
        json={"email": email, "alias": alias, "password": VALID_PASSWORD},
    )
    assert response.status_code == 201


def _publish_open(client, *, audience="public") -> str:
    session_response = client.post("/api/photo-upload-sessions")
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    image_ids = []
    for _ in range(2):
        upload = client.post(
            f"/api/photo-upload-sessions/{session_id}/images",
            files={"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")},
            data={"attempt_id": str(uuid.uuid4())},
        )
        assert upload.status_code == 201
        image_ids.append(upload.json()["id"])

    publish = client.post(
        "/api/consultations",
        json={
            "session_id": session_id,
            "ordered_image_ids": image_ids,
            "question": "Which one?",
            "context": None,
            "audience": audience,
        },
    )
    assert publish.status_code == 201
    return publish.json()["id"]


def test_delete_requires_authentication(client) -> None:
    response = client.post(
        f"/api/my-consultations/{uuid.uuid4()}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 401


def test_delete_open_returns_204_and_denies_all_reads(client, session_factory) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(f"/api/my-consultations/{consultation_id}").status_code == 404
    assert client.get("/api/my-consultations?state=open").json()["items"] == []
    assert client.get(f"/api/consultations/{consultation_id}").status_code == 404
    assert client.get(f"/api/my-consultations/{consultation_id}/results").status_code == 404
    assert client.get(f"/api/consultations/{consultation_id}/my-vote").status_code == 404


def test_delete_replay_returns_204(client) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    first = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    replay = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert first.status_code == 204
    assert replay.status_code == 204


def test_delete_stale_expected_state_conflicts(client, session_factory) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        consultation.state = ConsultationState.finalized
        db.commit()

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "consultation_conflict"}}


def test_delete_missing_is_404(client) -> None:
    _register(client)

    missing = client.post(
        f"/api/my-consultations/{uuid.uuid4()}/delete",
        json={"expected_state": "open"},
    )
    assert missing.status_code == 404
    assert missing.json() == {"detail": {"code": "consultation_unavailable"}}


def test_delete_foreign_owner_is_generic_404(client, session_factory) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    _register(client, email="bob@example.com", alias="Bob")

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "consultation_unavailable"}}

    # The foreign attempt changed nothing: the row remains open and unmarked.
    with session_factory() as db:
        row = db.get(Consultation, uuid.UUID(consultation_id))
        assert row.state == ConsultationState.open
        assert row.author_deleted_at is None


def test_delete_rejects_hostile_and_null_origin(client) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    for origin in ("https://evil.example", "null"):
        response = client.post(
            f"/api/my-consultations/{consultation_id}/delete",
            json={"expected_state": "open"},
            headers={"Origin": origin},
        )
        assert response.status_code == 403
        assert response.json() == {"detail": {"code": "origin_not_allowed"}}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"expected_state": "unknown"},
        {"expected_state": "open", "extra": True},
        {"expected_state": None},
    ],
)
def test_delete_strict_payload_validation(client, payload) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_delete_sets_private_headers(client) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 204
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_delete_removes_votes_from_live_results(client) -> None:
    _register(client)
    consultation_id = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/delete",
        json={"expected_state": "open"},
    )
    assert response.status_code == 204
    assert client.get(f"/api/my-consultations/{consultation_id}/results").status_code == 404


# --- Observability ------------------------------------------------------------------------


def test_deletion_logs_first_classification_without_content(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, with_votes=1)
        cid = consultation.id

        with caplog.at_level(logging.INFO, logger="app.consultation_deletion_service"):
            delete_consultation(db, cid, account.id, "open", now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=first" in message for message in messages)
    assert any(f"consultation_id={cid}" in message for message in messages)
    assert any("previous_lifecycle=open" in message for message in messages)
    assert any("votes_removed=1" in message for message in messages)
    assert any("images_marked=2" in message for message in messages)
    for message in messages:
        assert "Which one?" not in message
        assert "For LinkedIn" not in message


def test_replay_logs_source_lifecycle_open_for_deleted_marker(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id)
        cid = consultation.id

        delete_consultation(db, cid, account.id, "open", now=T0)
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.consultation_deletion_service"):
            delete_consultation(db, cid, account.id, "open", now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=replay" in message for message in messages)
    assert any("previous_lifecycle=open" in message for message in messages)


def test_replay_logs_source_lifecycle_finalized_for_finalized_marker(
    session_factory, caplog
) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized")
        cid = consultation.id

        delete_consultation(db, cid, account.id, "finalized", now=T0)
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.consultation_deletion_service"):
            delete_consultation(db, cid, account.id, "finalized", now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=replay" in message for message in messages)
    assert any("previous_lifecycle=finalized" in message for message in messages)


def test_deletion_logs_conflict_classification(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id, state="finalized")
        cid = consultation.id

        with caplog.at_level(logging.INFO, logger="app.consultation_deletion_service"):
            with pytest.raises(ConsultationConflictError):
                delete_consultation(db, cid, account.id, "open", now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=conflict" in message for message in messages)
    assert any(f"consultation_id={cid}" in message for message in messages)


def test_deletion_logs_error_classification_without_exception_text(
    session_factory, caplog, monkeypatch
) -> None:
    def boom(db, consultation, now=None):
        raise RuntimeError("sensitive marker failure detail")

    monkeypatch.setattr("app.consultation_deletion_service.mark_media_for_erasure", boom)

    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed_consultation(db, account.id)
        cid = consultation.id

        with caplog.at_level(logging.ERROR, logger="app.consultation_deletion_service"):
            with pytest.raises(RuntimeError):
                delete_consultation(db, cid, account.id, "open", now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=error" in message for message in messages)
    assert any(f"consultation_id={cid}" in message for message in messages)
    for message in messages:
        assert "sensitive marker failure detail" not in message


def test_deletion_does_not_log_for_missing_or_foreign_rows(session_factory, caplog) -> None:
    with session_factory() as db:
        owner = _account(db)
        other = _account(db, email="other@example.com", alias="Other")
        consultation, _, _, _ = _seed_consultation(db, owner.id)

        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.consultation_deletion_service"):
            with pytest.raises(ConsultationUnavailableError):
                delete_consultation(db, uuid.uuid4(), owner.id, "open", now=T0)
            with pytest.raises(ConsultationUnavailableError):
                delete_consultation(db, consultation.id, other.id, "open", now=T0)

    assert all("author deletion" not in record.message for record in caplog.records)
