import io
import logging
import uuid
from datetime import datetime, timezone

import pytest
from PIL import Image
from sqlalchemy import select

from app.consultation_finalization_service import (
    FinalizationDeclaration,
    FinalizationInvalidError,
    finalize_consultation,
)
from app.consultation_service import (
    ConsultationConflictError,
    ConsultationUnavailableError,
    list_my_consultations,
    read_my_consultation,
)
from app.finalization_summary import build_finalized_summary
from app.models import (
    Account,
    Consultation,
    ConsultationFinalization,
    ConsultationOutcome,
    ConsultationPhoto,
    ConsultationState,
    FinalizationOutcome,
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


def _seed(
    db, account_id, *, audience="public", state="open", option_count=2, votes=None, storage=None
) -> tuple[Consultation, list[PhotoUploadImage], list[ConsultationPhoto], PhotoUploadSession]:
    """Seed a consultation with ``option_count`` photos and optional votes.

    ``votes`` maps a photo index to the number of voter accounts voting for it.
    """
    session = PhotoUploadSession(
        account_id=account_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=T0,
    )
    db.add(session)
    db.flush()

    images: list[PhotoUploadImage] = []
    for _ in range(option_count):
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

    for index, count in (votes or {}).items():
        for _ in range(count):
            suffix = uuid.uuid4().hex[:8]
            voter = Account(
                email=f"voter{suffix}@example.com",
                alias=f"Voter{suffix}",
                alias_canonical=f"voter{suffix}".lower(),
                password_hash="x",
            )
            db.add(voter)
            db.flush()
            db.add(
                Vote(
                    consultation_id=consultation.id,
                    voter_id=voter.id,
                    consultation_photo_id=photos[index].id,
                )
            )

    db.commit()
    return consultation, images, photos, session


def _decl(option_ids, kind="selected") -> FinalizationDeclaration:
    return FinalizationDeclaration(kind=kind, option_ids=tuple(option_ids))


# --- Service: declaration and snapshot --------------------------------------------------


def test_finalize_single_selection_writes_full_record(session_factory, storage) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, images, photos, _ = _seed(db, account.id, votes={0: 2, 1: 1}, storage=storage)
        cid = consultation.id

        result = finalize_consultation(
            db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]), now=T0
        )

        assert result.classification == "first"
        assert result.summary.total_votes == 3
        assert result.summary.declaration == "selected"
        assert result.summary.selected_ordinals == [0]
        assert [o.vote_count for o in result.summary.options] == [2, 1]
        assert [o.selected for o in result.summary.options] == [True, False]
        assert result.matched == 2
        assert result.not_matched == 1
        assert result.no_choice == 0

        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.finalized
        assert row.question is None
        assert row.context is None
        assert row.audience is None
        assert row.fingerprint is None
        assert int(row.private_link_generation) == 0
        assert row.private_link_active is False
        assert row.author_deleted_at is None

        header = db.get(ConsultationFinalization, cid)
        assert header is not None
        assert header.total_votes == 3
        assert header.finalized_at is not None

    with session_factory() as db:
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is None
        outcomes = db.scalars(
            select(ConsultationOutcome).where(ConsultationOutcome.consultation_id == cid)
        ).all()
        assert {o.outcome for o in outcomes} == {
            FinalizationOutcome.matched,
            FinalizationOutcome.not_matched,
        }
        assert sum(1 for o in outcomes if o.outcome == FinalizationOutcome.matched) == 2
        assert sum(1 for o in outcomes if o.outcome == FinalizationOutcome.not_matched) == 1
        for image in images:
            assert db.get(PhotoUploadImage, image.id).state == PhotoImageState.revoked


def test_finalize_multiple_and_all_selections(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, option_count=3, votes={0: 1, 1: 1, 2: 1})

        result = finalize_consultation(
            db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id, photos[2].id])
        )

        assert result.summary.declaration == "selected"
        assert result.summary.selected_ordinals == [0, 2]
        assert result.matched == 2
        assert result.not_matched == 1


def test_finalize_none_produces_no_choice_for_every_voter(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 2, 1: 1})

        result = finalize_consultation(
            db, consultation.id, account.id, uuid.uuid4(), _decl([], kind="none")
        )

        assert result.summary.declaration == "none"
        assert result.summary.selected_ordinals == []
        assert [o.selected for o in result.summary.options] == [False, False]
        assert result.matched == 0
        assert result.not_matched == 0
        assert result.no_choice == 3

    with session_factory() as db:
        outcomes = db.scalars(
            select(ConsultationOutcome).where(
                ConsultationOutcome.consultation_id == consultation.id
            )
        ).all()
        assert {o.outcome for o in outcomes} == {FinalizationOutcome.no_choice}
        assert len(outcomes) == 3


def test_finalize_zero_votes_and_zero_vote_options(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, option_count=3)

        result = finalize_consultation(
            db, consultation.id, account.id, uuid.uuid4(), _decl([photos[1].id])
        )

        assert result.summary.total_votes == 0
        assert [o.vote_count for o in result.summary.options] == [0, 0, 0]
        assert [o.selected for o in result.summary.options] == [False, True, False]

    with session_factory() as db:
        assert (
            db.scalar(
                select(ConsultationOutcome).where(
                    ConsultationOutcome.consultation_id == consultation.id
                )
            )
            is None
        )


def test_finalize_majority_disagreement_is_valid(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 3, 1: 1})

        result = finalize_consultation(
            db, consultation.id, account.id, uuid.uuid4(), _decl([photos[1].id])
        )

        assert result.matched == 1
        assert result.not_matched == 3


# --- Service: identity, authorization and failures -------------------------------------


def test_exact_replay_is_idempotent(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})
        operation_id = uuid.uuid4()

        first = finalize_consultation(
            db, consultation.id, account.id, operation_id, _decl([photos[0].id]), now=T0
        )
        replay = finalize_consultation(
            db, consultation.id, account.id, operation_id, _decl([photos[0].id]), now=T0
        )

        assert first.classification == "first"
        assert replay.classification == "replay"
        assert replay.summary == first.summary


def test_same_operation_different_payload_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})
        operation_id = uuid.uuid4()

        finalize_consultation(db, consultation.id, account.id, operation_id, _decl([photos[0].id]))

        with pytest.raises(ConsultationConflictError):
            finalize_consultation(
                db, consultation.id, account.id, operation_id, _decl([photos[1].id])
            )


def test_new_operation_against_finalized_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})

        finalize_consultation(db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id]))

        with pytest.raises(ConsultationConflictError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id])
            )


def test_legacy_finalized_without_header_conflicts(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, state="finalized")

        with pytest.raises(ConsultationConflictError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id])
            )


def test_foreign_owner_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        other = _account(db, email="other@example.com", alias="Other")
        consultation, _, photos, _ = _seed(db, owner.id)

        with pytest.raises(ConsultationUnavailableError):
            finalize_consultation(
                db, consultation.id, other.id, uuid.uuid4(), _decl([photos[0].id])
            )


def test_unknown_consultation_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        with pytest.raises(ConsultationUnavailableError):
            finalize_consultation(db, uuid.uuid4(), account.id, uuid.uuid4(), _decl([]))


def test_removed_consultation_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, state="removed")

        with pytest.raises(ConsultationUnavailableError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id])
            )


def test_author_deleted_target_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, state="finalized")
        consultation.author_deleted_at = T0
        db.commit()

        with pytest.raises(ConsultationUnavailableError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id])
            )


@pytest.mark.parametrize(
    "kind, option_ids, valid",
    [
        ("selected", [], False),
        ("selected", ["dup", "dup"], False),
        ("none", ["00000000-0000-0000-0000-000000000000"], False),
    ],
)
def test_invalid_declarations_are_rejected(session_factory, kind, option_ids, valid) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id)

        if kind == "selected" and option_ids == ["dup", "dup"]:
            ids = [photos[0].id, photos[0].id]
        elif kind == "selected" and option_ids == []:
            ids = []
        else:
            ids = [uuid.UUID(option_ids[0])]

        with pytest.raises(FinalizationInvalidError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl(ids, kind=kind)
            )


def test_foreign_option_reference_is_invalid(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id)
        other, _, other_photos, _ = _seed(db, account.id)

        with pytest.raises(FinalizationInvalidError):
            finalize_consultation(
                db, consultation.id, account.id, uuid.uuid4(), _decl([other_photos[0].id])
            )


def test_finalize_rolls_back_on_marker_failure(session_factory, monkeypatch) -> None:
    def boom(db, consultation, now=None):
        raise RuntimeError("marker failure")

    monkeypatch.setattr("app.consultation_finalization_service.mark_media_for_erasure", boom)

    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})
        cid = consultation.id

        with pytest.raises(RuntimeError):
            finalize_consultation(db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]))

    with session_factory() as db:
        row = db.get(Consultation, cid)
        assert row.state == ConsultationState.open
        assert row.question == "Which one?"
        assert db.scalar(select(Vote).where(Vote.consultation_id == cid)) is not None
        assert db.get(ConsultationFinalization, cid) is None


def test_finalize_converges_through_rf37_reconciliation(session_factory, storage) -> None:
    from app.photo_erasure_service import reconcile_terminal_media

    with session_factory() as db:
        account = _account(db)
        consultation, images, photos, source_session = _seed(
            db, account.id, storage=storage, votes={0: 1}
        )
        cid = consultation.id
        keys = [image.storage_key for image in images]

        finalize_consultation(db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]), now=T0)

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
        summary = build_finalized_summary(db, cid)
        assert summary is not None
        assert [o.vote_count for o in summary.options] == [1, 0]


# --- Owner projections ----------------------------------------------------------------


def test_finalized_list_and_detail_show_result(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 2, 1: 1})
        finalize_consultation(db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id]))

        detail = read_my_consultation(db, consultation.id, account.id)
        assert detail.state == "finalized"
        assert detail.result is not None
        assert detail.result.total_votes == 3
        assert detail.result.declaration == "selected"
        assert detail.result.selected_ordinals == [0]

        listing = list_my_consultations(db, account.id, "finalized", 20, None)
        assert len(listing.items) == 1
        item = listing.items[0]
        assert item.result is not None
        assert item.result.selected_ordinals == [0]


def test_legacy_finalized_detail_has_no_result(session_factory) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, _, _ = _seed(db, account.id, state="finalized")

        detail = read_my_consultation(db, consultation.id, account.id)
        assert detail.result is None


def test_finalized_withdrawal_preserves_result(session_factory) -> None:
    from app.consultation_deletion_service import delete_consultation

    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})
        finalize_consultation(db, consultation.id, account.id, uuid.uuid4(), _decl([photos[0].id]))

        delete_consultation(db, consultation.id, account.id, "finalized", now=T0)

        row = db.get(Consultation, consultation.id)
        assert row.state == ConsultationState.finalized
        assert row.author_deleted_at is not None
        assert db.get(ConsultationFinalization, consultation.id) is not None


# --- Observability --------------------------------------------------------------------


def test_finalize_logs_first_without_content(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 2, 1: 1})
        cid = consultation.id

        with caplog.at_level(logging.INFO, logger="app.consultation_finalization_service"):
            finalize_consultation(db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]), now=T0)

    messages = [record.message for record in caplog.records]
    assert any("classification=first" in m for m in messages)
    assert any(f"consultation_id={cid}" in m for m in messages)
    assert any("total_votes=3" in m for m in messages)
    assert any("selected_count=1" in m for m in messages)
    assert any("matched=2" in m for m in messages)
    assert any("not_matched=1" in m for m in messages)
    assert any("images_marked=2" in m for m in messages)
    for message in messages:
        assert "Which one?" not in message
        assert "For LinkedIn" not in message
        assert str(photos[0].id) not in message


def test_finalize_logs_replay(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, votes={0: 1})
        operation_id = uuid.uuid4()
        finalize_consultation(db, consultation.id, account.id, operation_id, _decl([photos[0].id]))
        caplog.clear()

        with caplog.at_level(logging.INFO, logger="app.consultation_finalization_service"):
            finalize_consultation(
                db, consultation.id, account.id, operation_id, _decl([photos[0].id])
            )

    messages = [record.message for record in caplog.records]
    assert any("classification=replay" in m for m in messages)


def test_finalize_logs_conflict(session_factory, caplog) -> None:
    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id, state="finalized")
        cid = consultation.id

        with caplog.at_level(logging.INFO, logger="app.consultation_finalization_service"):
            with pytest.raises(ConsultationConflictError):
                finalize_consultation(db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]))

    messages = [record.message for record in caplog.records]
    assert any("classification=conflict" in m for m in messages)


def test_finalize_logs_error_without_exception_text(session_factory, caplog, monkeypatch) -> None:
    def boom(db, consultation, now=None):
        raise RuntimeError("sensitive marker failure detail")

    monkeypatch.setattr("app.consultation_finalization_service.mark_media_for_erasure", boom)

    with session_factory() as db:
        account = _account(db)
        consultation, _, photos, _ = _seed(db, account.id)
        cid = consultation.id

        with caplog.at_level(logging.ERROR, logger="app.consultation_finalization_service"):
            with pytest.raises(RuntimeError):
                finalize_consultation(db, cid, account.id, uuid.uuid4(), _decl([photos[0].id]))

    messages = [record.message for record in caplog.records]
    assert any("classification=error" in m for m in messages)
    for message in messages:
        assert "sensitive marker failure detail" not in message


# --- API tests -----------------------------------------------------------------------


def _register(client, email="ana@example.com", alias="Ana") -> None:
    response = client.post(
        "/api/accounts",
        json={"email": email, "alias": alias, "password": VALID_PASSWORD},
    )
    assert response.status_code == 201


def _publish_open(client, *, audience="public", count=2) -> tuple[str, list[str]]:
    session_response = client.post("/api/photo-upload-sessions")
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    image_ids = []
    for _ in range(count):
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
    consultation_id = publish.json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    return consultation_id, photo_ids


def _finalize_payload(photo_ids, *, operation_id=None, kind="selected"):
    return {
        "operation_id": str(operation_id or uuid.uuid4()),
        "expected_state": "open",
        "declaration": {"kind": kind, "option_ids": photo_ids},
    }


def test_finalize_requires_authentication(client) -> None:
    response = client.post(
        f"/api/my-consultations/{uuid.uuid4()}/finalize",
        json=_finalize_payload([]),
    )
    assert response.status_code == 401


def test_finalize_selected_returns_summary_and_denies_reads(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "finalized"
    assert body["result"]["declaration"] == "selected"
    assert body["result"]["selected_ordinals"] == [0]
    assert body["result"]["total_votes"] == 0
    assert [o["vote_count"] for o in body["result"]["options"]] == [0, 0]
    assert [o["selected"] for o in body["result"]["options"]] == [True, False]

    assert client.get(f"/api/my-consultations/{consultation_id}").json()["result"] is not None
    assert client.get(f"/api/consultations/{consultation_id}").status_code == 404
    assert client.get(f"/api/my-consultations/{consultation_id}/results").status_code == 404
    assert (
        client.get(
            f"/api/consultations/{consultation_id}/photos/{photo_ids[0]}/content"
        ).status_code
        == 404
    )
    assert client.get(f"/api/consultations/{consultation_id}/my-vote").status_code == 404


def test_finalize_none_returns_no_choice_summary(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([], kind="none"),
    )
    assert response.status_code == 200
    assert response.json()["result"]["declaration"] == "none"
    assert response.json()["result"]["selected_ordinals"] == []


def test_finalize_replay_returns_same_summary(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)
    operation_id = uuid.uuid4()

    first = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]], operation_id=operation_id),
    )
    replay = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]], operation_id=operation_id),
    )
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()


def test_finalize_conflict_returns_409(client, session_factory) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    first = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert first.status_code == 200

    conflict = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert conflict.status_code == 409
    assert conflict.json() == {"detail": {"code": "consultation_conflict"}}


def test_finalize_invalid_declaration_returns_422(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    for payload in [
        {
            "operation_id": str(uuid.uuid4()),
            "expected_state": "open",
            "declaration": {"kind": "selected", "option_ids": []},
        },
        {
            "operation_id": str(uuid.uuid4()),
            "expected_state": "open",
            "declaration": {"kind": "none", "option_ids": [photo_ids[0]]},
        },
        {
            "operation_id": str(uuid.uuid4()),
            "expected_state": "open",
            "declaration": {"kind": "selected", "option_ids": [photo_ids[0], photo_ids[0]]},
        },
    ]:
        response = client.post(f"/api/my-consultations/{consultation_id}/finalize", json=payload)
        assert response.status_code == 422, payload


def test_finalize_foreign_option_returns_422(client) -> None:
    _register(client)
    consultation_id, _ = _publish_open(client)
    other_id, other_photos = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([other_photos[0]]),
    )
    assert response.status_code == 422


def test_finalize_missing_and_foreign_are_404(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    missing = client.post(
        f"/api/my-consultations/{uuid.uuid4()}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert missing.status_code == 404

    _register(client, email="bob@example.com", alias="Bob")
    foreign = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert foreign.status_code == 404
    assert foreign.json() == {"detail": {"code": "consultation_unavailable"}}


def test_finalize_rejects_hostile_and_null_origin(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    for origin in ("https://evil.example", "null"):
        response = client.post(
            f"/api/my-consultations/{consultation_id}/finalize",
            json=_finalize_payload([photo_ids[0]]),
            headers={"Origin": origin},
        )
        assert response.status_code == 403
        assert response.json() == {"detail": {"code": "origin_not_allowed"}}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"operation_id": str(uuid.uuid4())},
        {
            "operation_id": str(uuid.uuid4()),
            "expected_state": "finalized",
            "declaration": {"kind": "none", "option_ids": []},
        },
        {
            "operation_id": str(uuid.uuid4()),
            "expected_state": "open",
            "declaration": {"kind": "none", "option_ids": []},
            "extra": True,
        },
    ],
)
def test_finalize_strict_payload_validation(client, payload) -> None:
    _register(client)
    consultation_id, _ = _publish_open(client)

    response = client.post(f"/api/my-consultations/{consultation_id}/finalize", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_finalize_sets_private_headers(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    response = client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_finalized_list_shows_declaration_for_new_finalization(client) -> None:
    _register(client)
    consultation_id, photo_ids = _publish_open(client)

    client.post(
        f"/api/my-consultations/{consultation_id}/finalize",
        json=_finalize_payload([photo_ids[0]]),
    )

    body = client.get("/api/my-consultations?state=finalized").json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["result"]["declaration"] == "selected"
    assert item["result"]["selected_ordinals"] == [0]


def test_legacy_finalized_list_shows_result_unavailable(client, session_factory) -> None:
    from app.models import Consultation

    _register(client)
    consultation_id, _ = _publish_open(client)
    with session_factory() as db:
        consultation = db.get(Consultation, uuid.UUID(consultation_id))
        consultation.state = ConsultationState.finalized
        db.commit()

    body = client.get("/api/my-consultations?state=finalized").json()
    assert body["items"][0]["result"] is None
