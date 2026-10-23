import uuid
from datetime import datetime

import pytest
from sqlalchemy import delete

from app.consultation_deletion_service import delete_consultation
from app.consultation_finalization_service import (
    FinalizationDeclaration,
    finalize_consultation,
)
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
from app.participation_service import (
    decode_history_cursor,
    encode_history_cursor,
    list_participation_history,
)

T0 = datetime(2026, 1, 1, 12, 0, 0)
SNAPSHOT = datetime(2030, 1, 1, 0, 0, 0)


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


def _consultation(
    db,
    owner_id,
    *,
    audience="public",
    state="open",
    published_at=T0,
) -> tuple[Consultation, list[ConsultationPhoto]]:
    session = PhotoUploadSession(
        account_id=owner_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=T0,
    )
    db.add(session)
    db.flush()

    images: list[PhotoUploadImage] = []
    for _ in range(2):
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=uuid.uuid4().hex,
            width=10,
            height=10,
        )
        db.add(image)
        db.flush()
        images.append(image)

    consultation = Consultation(
        owner_id=owner_id,
        question="Which one?",
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
    db.flush()

    photos: list[ConsultationPhoto] = []
    for ordinal, image in enumerate(images):
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo)

    db.commit()
    return consultation, photos


def _vote(db, consultation_id, voter_id, photo_id, created_at=T0) -> None:
    db.add(
        Vote(
            consultation_id=consultation_id,
            voter_id=voter_id,
            consultation_photo_id=photo_id,
            created_at=created_at,
        )
    )
    db.commit()


def _finalize(db, consultation_id, owner_id, option_ids, *, kind="selected", now=T0) -> None:
    finalize_consultation(
        db,
        consultation_id,
        owner_id,
        uuid.uuid4(),
        FinalizationDeclaration(kind=kind, option_ids=tuple(option_ids)),
        now=now,
    )


def _list(db, account_id, *, limit=20, cursor=None, now=SNAPSHOT):
    return list_participation_history(db, account_id, limit, cursor, now=now)


# --- Row derivation ----------------------------------------------------------------


def test_open_public_vote_is_open_and_viewable(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id, audience="public")
        _vote(db, consultation.id, voter.id, photos[0].id, created_at=datetime(2026, 2, 1))

        page = _list(db, voter.id)

    assert len(page.items) == 1
    item = page.items[0]
    assert item.consultation_id == str(consultation.id)
    assert item.status == "open"
    assert item.event_kind == "voted"
    assert item.event_at == datetime(2026, 2, 1)
    assert item.can_view is True


def test_open_private_vote_is_open_and_not_viewable(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id, audience="private")
        _vote(db, consultation.id, voter.id, photos[0].id)

        page = _list(db, voter.id)

    assert len(page.items) == 1
    assert page.items[0].status == "open"
    assert page.items[0].can_view is False


def test_only_current_account_rows_are_returned(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        alice = _account(db, email="alice@example.com", alias="Alice")
        bob = _account(db, email="bob@example.com", alias="Bob")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, alice.id, photos[0].id)

        alice_page = _list(db, alice.id)
        bob_page = _list(db, bob.id)
        owner_page = _list(db, owner.id)

    assert len(alice_page.items) == 1
    assert bob_page.items == []
    assert owner_page.items == []


def test_matched_not_matched_no_choice_mapping(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        matched = _account(db, email="m@example.com", alias="M")
        not_matched = _account(db, email="n@example.com", alias="N")
        consultation, photos = _consultation(db, owner.id)
        finalized_at = datetime(2026, 3, 1, 9, 30, 0)
        _vote(db, consultation.id, matched.id, photos[0].id)
        _vote(db, consultation.id, not_matched.id, photos[1].id)
        _finalize(db, consultation.id, owner.id, [photos[0].id], now=finalized_at)

        matched_page = _list(db, matched.id)
        not_matched_page = _list(db, not_matched.id)

    assert matched_page.items[0].status == "matched"
    assert matched_page.items[0].event_kind == "finalized"
    assert matched_page.items[0].event_at == finalized_at
    assert matched_page.items[0].can_view is False
    assert not_matched_page.items[0].status == "not_matched"


def test_no_choice_mapping(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id)
        _finalize(db, consultation.id, owner.id, [], kind="none", now=datetime(2026, 3, 1))

        page = _list(db, voter.id)

    assert page.items[0].status == "no_choice"
    assert page.items[0].event_kind == "finalized"


def test_author_deleted_final_consultation_keeps_outcome(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id)
        _finalize(db, consultation.id, owner.id, [photos[0].id], now=datetime(2026, 3, 1))
        delete_consultation(db, consultation.id, owner.id, "finalized", now=datetime(2026, 3, 2))

        page = _list(db, voter.id)

    assert len(page.items) == 1
    assert page.items[0].status == "matched"


def test_open_deletion_leaves_no_row(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id)
        delete_consultation(db, consultation.id, owner.id, "open", now=datetime(2026, 3, 1))

        page = _list(db, voter.id)

    assert page.items == []
    assert page.next_cursor is None


def test_removed_open_participation_leaves_no_row(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id)
        db.execute(delete(Vote).where(Vote.consultation_id == consultation.id))
        consultation.state = ConsultationState.removed
        db.commit()

        page = _list(db, voter.id)

    assert page.items == []


def test_terminal_residual_vote_maps_to_unavailable(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id, state="finalized")
        _vote(db, consultation.id, voter.id, photos[0].id, created_at=datetime(2026, 2, 1))

        page = _list(db, voter.id)

    assert len(page.items) == 1
    assert page.items[0].status == "unavailable"
    assert page.items[0].event_kind == "voted"
    assert page.items[0].event_at == datetime(2026, 2, 1)
    assert page.items[0].can_view is False


def test_legacy_finalized_without_proof_is_omitted(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        _consultation(db, owner.id, state="finalized")

        page = _list(db, voter.id)

    assert page.items == []


def test_outcome_has_precedence_over_residual_vote(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id)
        _finalize(db, consultation.id, owner.id, [photos[0].id], now=datetime(2026, 3, 1))

        # Reinsert a residual vote alongside the outcome to prove no duplicate row is produced.
        _vote(db, consultation.id, voter.id, photos[0].id, created_at=datetime(2026, 2, 1))

        page = _list(db, voter.id)

    assert len(page.items) == 1
    assert page.items[0].status == "matched"


def test_outcome_has_precedence_over_open_state_residual_vote(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        consultation, photos = _consultation(db, owner.id)
        _vote(db, consultation.id, voter.id, photos[0].id, created_at=datetime(2026, 2, 1))

        # Simulate inconsistent storage that remains physically valid: an outcome and its
        # finalization header exist while the consultation and residual vote are still open.
        db.add(
            ConsultationFinalization(
                consultation_id=consultation.id,
                operation_id=uuid.uuid4(),
                payload_fingerprint=uuid.uuid4().hex,
                finalized_at=datetime(2026, 3, 1),
                total_votes=1,
            )
        )
        db.add(
            ConsultationOutcome(
                consultation_id=consultation.id,
                voter_id=voter.id,
                outcome=FinalizationOutcome.matched,
            )
        )
        db.commit()

        page = _list(db, voter.id)

    assert len(page.items) == 1
    assert page.items[0].status == "matched"
    assert page.items[0].event_kind == "finalized"


# --- Ordering and pagination --------------------------------------------------------


def test_mixed_history_orders_newest_first_with_tiebreak(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")

        open_a, photos_a = _consultation(db, owner.id, published_at=T0)
        open_b, photos_b = _consultation(db, owner.id, published_at=T0)
        _vote(db, open_a.id, voter.id, photos_a[0].id, created_at=datetime(2026, 2, 1))
        _vote(db, open_b.id, voter.id, photos_b[0].id, created_at=datetime(2026, 2, 1))

        done, done_photos = _consultation(db, owner.id, published_at=T0)
        _vote(db, done.id, voter.id, done_photos[0].id, created_at=datetime(2026, 1, 1))
        _finalize(db, done.id, owner.id, [done_photos[0].id], now=datetime(2026, 4, 1))

        page = _list(db, voter.id)

    statuses = [item.status for item in page.items]
    assert statuses[0] == "matched"
    assert {item.consultation_id for item in page.items[1:]} == {str(open_a.id), str(open_b.id)}
    assert page.items[1].status == "open"
    assert page.items[2].status == "open"


def test_multiple_pages_do_not_duplicate_or_skip(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        ids: list[str] = []
        for index in range(25):
            consultation, photos = _consultation(db, owner.id, published_at=T0)
            _vote(
                db,
                consultation.id,
                voter.id,
                photos[0].id,
                created_at=datetime(2026, 1, 1, 0, 0, index),
            )
            ids.append(str(consultation.id))

    collected: list[str] = []
    cursor = None
    while True:
        page = _list(db, voter.id, limit=20, cursor=cursor)
        collected.extend(item.consultation_id for item in page.items)
        if page.next_cursor is None:
            break
        cursor = decode_history_cursor(page.next_cursor)

    assert len(collected) == len(set(collected)) == 25
    assert set(collected) == set(ids)


def test_tied_timestamps_use_consultation_id_tiebreak(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        ids: list[str] = []
        for _ in range(3):
            consultation, photos = _consultation(db, owner.id, published_at=T0)
            _vote(db, consultation.id, voter.id, photos[0].id, created_at=datetime(2026, 1, 1))
            ids.append(str(consultation.id))

        collected: list[str] = []
        cursor = None
        while True:
            page = _list(db, voter.id, limit=1, cursor=cursor)
            collected.extend(item.consultation_id for item in page.items)
            if page.next_cursor is None:
                break
            cursor = decode_history_cursor(page.next_cursor)

    assert len(collected) == len(set(collected)) == 3
    assert set(collected) == set(ids)


def test_new_finalization_after_snapshot_disappears_from_older_page(session_factory) -> None:
    with session_factory() as db:
        owner = _account(db)
        voter = _account(db, email="voter@example.com", alias="Voter")
        older, older_photos = _consultation(db, owner.id)
        _vote(db, older.id, voter.id, older_photos[0].id, created_at=datetime(2025, 12, 1))
        newer, newer_photos = _consultation(db, owner.id)
        _vote(db, newer.id, voter.id, newer_photos[0].id, created_at=datetime(2026, 1, 1))

        first = _list(db, voter.id, limit=1, now=datetime(2026, 2, 1))
        assert first.items[0].consultation_id == str(newer.id)
        assert first.next_cursor is not None

        _finalize(db, newer.id, owner.id, [newer_photos[0].id], now=datetime(2026, 3, 1))

        second = _list(db, voter.id, limit=1, cursor=decode_history_cursor(first.next_cursor))

    # The final event is newer than the first-page snapshot, so the second (older) page shows only
    # the older open vote, never the just-finalized outcome.
    assert len(second.items) == 1
    assert second.items[0].consultation_id == str(older.id)
    assert second.items[0].status == "open"


# --- Cursor codec -------------------------------------------------------------------


def test_cursor_roundtrip(session_factory) -> None:
    cid = uuid.uuid4()
    snapshot = datetime(2030, 1, 1)
    event = datetime(2026, 5, 1)
    raw = encode_history_cursor(snapshot, event, cid)
    assert decode_history_cursor(raw) == (snapshot, event, cid)


@pytest.mark.parametrize(
    "raw",
    [
        "not-base64!!!",
        "a" * 600,
        "%%%",
        "",
    ],
)
def test_malformed_cursor_is_rejected(raw) -> None:
    assert decode_history_cursor(raw) is None


def test_wrong_version_cursor_is_rejected() -> None:
    import base64
    import json

    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                ["v9", "2030-01-01T00:00:00", "2026-01-01T00:00:00", str(uuid.uuid4())]
            ).encode()
        )
        .decode()
        .rstrip("=")
    )
    assert decode_history_cursor(payload) is None


def test_event_after_snapshot_cursor_is_rejected() -> None:
    cid = uuid.uuid4()
    raw = encode_history_cursor(datetime(2026, 1, 1), datetime(2026, 2, 1), cid)
    assert decode_history_cursor(raw) is None


# --- API tests ----------------------------------------------------------------------


import io  # noqa: E402

from PIL import Image  # noqa: E402

VALID_PASSWORD = "correct-horse-battery-staple"


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 30, 30)).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _register(client, email="ana@example.com", alias="Ana") -> None:
    response = client.post(
        "/api/accounts",
        json={"email": email, "alias": alias, "password": VALID_PASSWORD},
    )
    assert response.status_code == 201


def _publish(client, *, audience="public") -> tuple[str, list[str]]:
    session_response = client.post("/api/photo-upload-sessions")
    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    image_ids: list[str] = []
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
    consultation_id = publish.json()["id"]
    detail = client.get(f"/api/consultations/{consultation_id}").json()
    photo_ids = [photo["id"] for photo in detail["photos"]]
    return consultation_id, photo_ids


def test_my_participation_requires_authentication(client) -> None:
    response = client.get("/api/my-participation")
    assert response.status_code == 401
    assert response.headers["cache-control"] == "private, no-store"


def test_empty_history_is_distinct_from_failure(client) -> None:
    _register(client)
    response = client.get("/api/my-participation")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}


def test_private_read_headers_are_present(client) -> None:
    _register(client)
    response = client.get("/api/my-participation")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_open_public_row_exposes_only_allowlisted_fields(client) -> None:
    _register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish(client)

    _register(client, email="bob@example.com", alias="Bob")
    vote = client.post(
        f"/api/consultations/{consultation_id}/votes",
        json={"photo_id": photo_ids[0]},
    )
    assert vote.status_code == 201

    response = client.get("/api/my-participation")
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == {"consultation_id", "status", "event_kind", "event_at", "can_view"}
    assert item["consultation_id"] == consultation_id
    assert item["status"] == "open"
    assert item["event_kind"] == "voted"
    assert item["event_at"].endswith("Z")
    assert item["can_view"] is True


def test_cross_account_isolation(client) -> None:
    _register(client, email="ana@example.com", alias="Ana")
    consultation_id, photo_ids = _publish(client)

    _register(client, email="bob@example.com", alias="Bob")
    client.post(f"/api/consultations/{consultation_id}/votes", json={"photo_id": photo_ids[0]})

    _register(client, email="carol@example.com", alias="Carol")
    response = client.get("/api/my-participation")
    assert response.json() == {"items": [], "next_cursor": None}


@pytest.mark.parametrize("limit", [0, 51])
def test_limit_bounds_are_enforced(client, limit) -> None:
    _register(client)
    response = client.get(f"/api/my-participation?limit={limit}")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_api_malformed_cursor_is_rejected(client) -> None:
    _register(client)
    for cursor in ("not-base64!!!", "a" * 600, "%%%"):
        response = client.get(f"/api/my-participation?cursor={cursor}")
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "validation_error"
