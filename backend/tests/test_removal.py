import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.consultation_removal_service import (
    RemovalConsistencyError,
    RemovalInvalidError,
    remove_consultation,
)
from app.consultation_service import (
    ConsultationConflictError,
    ConsultationUnavailableError,
    list_feed,
    read_consultation_detail,
    read_consultation_photo,
)
from app.models import (
    Account,
    Consultation,
    ConsultationFinalization,
    ConsultationPhoto,
    ConsultationRemoval,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
    Vote,
)
from app.participation_service import list_participation_history
from app.photo_erasure_service import reconcile_terminal_media
from app.vote_service import submit_vote

T0 = datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc)


def _account(db, prefix: str) -> Account:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"{prefix}{suffix}@example.com",
        alias=f"{prefix}{suffix}",
        alias_canonical=f"{prefix}{suffix}".lower(),
        password_hash="x",
    )
    db.add(account)
    db.flush()
    return account


def _consultation(db, *, state: ConsultationState = ConsultationState.open, votes: int = 2):
    owner = _account(db, "Owner")
    upload = PhotoUploadSession(
        account_id=owner.id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=T0,
    )
    db.add(upload)
    db.flush()
    consultation = Consultation(
        owner_id=owner.id,
        question="Which one?",
        context="Context",
        audience="private",
        state=state,
        published_at=T0,
        source_session_id=upload.id,
        fingerprint=uuid.uuid4().hex,
        private_link_generation=1,
        private_link_active=True,
    )
    db.add(consultation)
    db.flush()
    image_ids: list[uuid.UUID] = []
    photo_ids: list[uuid.UUID] = []
    for ordinal in range(2):
        image = PhotoUploadImage(
            upload_session_id=upload.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=uuid.uuid4().hex,
            width=64,
            height=64,
        )
        db.add(image)
        db.flush()
        photo = ConsultationPhoto(
            consultation_id=consultation.id,
            image_id=image.id,
            ordinal=ordinal,
        )
        db.add(photo)
        db.flush()
        image_ids.append(image.id)
        photo_ids.append(photo.id)
    for index in range(votes):
        voter = _account(db, f"Voter{index}")
        db.add(
            Vote(
                consultation_id=consultation.id,
                voter_id=voter.id,
                consultation_photo_id=photo_ids[0],
            )
        )
    db.commit()
    return consultation.id, upload.id, image_ids


def _remove(db, consultation_id: uuid.UUID, operation_id: uuid.UUID, **overrides):
    return remove_consultation(
        db,
        consultation_id=consultation_id,
        operation_id=operation_id,
        expected_state=overrides.get("expected_state", "open"),
        operator_id=overrides.get("operator_id", "ops.alice"),
        reason_code=overrides.get("reason_code", "rights_or_privacy"),
        now=overrides.get("now", T0),
    )


def test_removal_atomically_records_audit_revokes_media_and_deletes_votes(
    session_factory,
) -> None:
    with session_factory() as db:
        consultation_id, _, image_ids = _consultation(db)
        operation_id = uuid.uuid4()

        result = _remove(db, consultation_id, operation_id)

        assert result.classification == "first"
        assert result.votes_removed == 2
        assert result.images_marked == 2

    with session_factory() as db:
        row = db.get(Consultation, consultation_id)
        assert row is not None
        assert row.state == ConsultationState.removed
        assert row.question is None
        assert row.context is None
        assert row.audience is None
        assert row.fingerprint is None
        assert int(row.private_link_generation) == 0
        assert row.private_link_active is False
        assert db.scalar(select(func.count()).select_from(Vote)) == 0
        audit = db.get(ConsultationRemoval, consultation_id)
        assert audit is not None
        assert audit.operation_id == operation_id
        assert audit.operator_id == "ops.alice"
        assert audit.reason_code == "rights_or_privacy"
        assert audit.previous_state == "open"
        for image_id in image_ids:
            image = db.get(PhotoUploadImage, image_id)
            assert image is not None
            assert image.state == PhotoImageState.revoked
            assert image.deletion_requested_at is not None


def test_exact_replay_has_no_repeated_side_effects(session_factory) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, votes=1)
        operation_id = uuid.uuid4()
        first = _remove(db, consultation_id, operation_id)
        replay = _remove(db, consultation_id, operation_id, now=T0.replace(hour=13))

        assert first.classification == "first"
        assert replay.classification == "replay"
        assert replay.removed_at.replace(tzinfo=timezone.utc) == first.removed_at
        assert replay.votes_removed == 0
        assert replay.images_marked == 0


@pytest.mark.parametrize(
    "change",
    [
        {"operation": True},
        {"operator_id": "ops.bob"},
        {"reason_code": "other"},
    ],
)
def test_mismatched_replay_conflicts(session_factory, change) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db)
        operation_id = uuid.uuid4()
        _remove(db, consultation_id, operation_id)
        retry_operation = uuid.uuid4() if change.get("operation") else operation_id

        with pytest.raises(ConsultationConflictError):
            _remove(
                db,
                consultation_id,
                retry_operation,
                **{k: v for k, v in change.items() if k != "operation"},
            )


def test_operation_id_cannot_be_reused_for_another_consultation(session_factory) -> None:
    with session_factory() as db:
        first_id, _, _ = _consultation(db)
        second_id, _, _ = _consultation(db)
        operation_id = uuid.uuid4()
        _remove(db, first_id, operation_id)

        with pytest.raises(ConsultationConflictError):
            _remove(db, second_id, operation_id)

        assert db.get(Consultation, second_id).state == ConsultationState.open


@pytest.mark.parametrize("state", [ConsultationState.finalized, ConsultationState.deleted])
def test_other_terminal_states_conflict(session_factory, state) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, state=state, votes=0)
        with pytest.raises(ConsultationConflictError):
            _remove(db, consultation_id, uuid.uuid4())
        assert db.get(ConsultationRemoval, consultation_id) is None


def test_historical_removed_without_audit_is_not_a_replay(session_factory) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, state=ConsultationState.removed, votes=0)
        with pytest.raises(ConsultationConflictError):
            _remove(db, consultation_id, uuid.uuid4())
        assert db.get(ConsultationRemoval, consultation_id) is None


def test_unknown_target_is_unavailable(session_factory) -> None:
    with session_factory() as db:
        with pytest.raises(ConsultationUnavailableError):
            _remove(db, uuid.uuid4(), uuid.uuid4())


def test_open_row_with_finalization_data_is_rejected(session_factory) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, votes=1)
        db.add(
            ConsultationFinalization(
                consultation_id=consultation_id,
                operation_id=uuid.uuid4(),
                payload_fingerprint="x" * 64,
                finalized_at=T0,
                total_votes=1,
            )
        )
        db.commit()

        with pytest.raises(RemovalConsistencyError):
            _remove(db, consultation_id, uuid.uuid4())

        assert db.get(Consultation, consultation_id).state == ConsultationState.open
        assert db.scalar(select(func.count()).select_from(Vote)) == 1


def test_erasure_precondition_failure_rolls_back_every_change(session_factory) -> None:
    with session_factory() as db:
        consultation_id, upload_id, image_ids = _consultation(db, votes=1)
        upload = db.get(PhotoUploadSession, upload_id)
        assert upload is not None
        upload.state = PhotoUploadSessionState.active
        db.commit()

        with pytest.raises(Exception, match="source session is not consumed"):
            _remove(db, consultation_id, uuid.uuid4())

    with session_factory() as db:
        assert db.get(Consultation, consultation_id).state == ConsultationState.open
        assert db.scalar(select(func.count()).select_from(Vote)) == 1
        assert db.get(ConsultationRemoval, consultation_id) is None
        for image_id in image_ids:
            assert db.get(PhotoUploadImage, image_id).state == PhotoImageState.ready


def test_service_rejects_non_open_contract_and_unknown_reason(session_factory) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db)
        with pytest.raises(RemovalInvalidError):
            _remove(db, consultation_id, uuid.uuid4(), expected_state="finalized")
        with pytest.raises(RemovalInvalidError):
            _remove(db, consultation_id, uuid.uuid4(), reason_code="free text")


def test_removal_makes_open_participation_history_disappear(session_factory) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, votes=1)
        voter_id = db.scalar(select(Vote.voter_id).where(Vote.consultation_id == consultation_id))
        assert voter_id is not None
        before = list_participation_history(
            db,
            voter_id,
            limit=20,
            cursor=None,
            now=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        assert [item.consultation_id for item in before.items] == [str(consultation_id)]

        _remove(db, consultation_id, uuid.uuid4())
        after = list_participation_history(
            db,
            voter_id,
            limit=20,
            cursor=None,
            now=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        assert after.items == []


def test_rf37_reconciliation_erases_bytes_without_changing_audit(session_factory, storage) -> None:
    with session_factory() as db:
        consultation_id, _, image_ids = _consultation(db, votes=1)
        storage_keys: list[str] = []
        for image_id in image_ids:
            image = db.get(PhotoUploadImage, image_id)
            assert image is not None and image.storage_key is not None
            storage.write_normalized(image.storage_key, b"private bytes")
            storage_keys.append(image.storage_key)
        operation_id = uuid.uuid4()
        _remove(db, consultation_id, operation_id)

        report = reconcile_terminal_media(db, storage, now=T0.replace(hour=13))
        assert report.objects_failed == 0
        assert report.sessions_completed == 1

    for storage_key in storage_keys:
        assert storage.exists(storage_key) is False
    with session_factory() as db:
        row = db.get(Consultation, consultation_id)
        assert row is not None
        assert row.state == ConsultationState.removed
        assert row.source_session_id is None
        audit = db.get(ConsultationRemoval, consultation_id)
        assert audit is not None
        assert audit.operation_id == operation_id


def test_committed_removal_immediately_denies_all_product_access(session_factory, storage) -> None:
    with session_factory() as db:
        consultation_id, _, _ = _consultation(db, votes=0)
        consultation = db.get(Consultation, consultation_id)
        assert consultation is not None
        owner_id = consultation.owner_id
        reader = _account(db, "Reader")
        reader_id = reader.id
        photo_id = db.scalar(
            select(ConsultationPhoto.id).where(ConsultationPhoto.consultation_id == consultation_id)
        )
        assert photo_id is not None
        db.commit()
        _remove(db, consultation_id, uuid.uuid4())

        feed = list_feed(db, reader_id, 20, None)
        assert all(item.id != str(consultation_id) for item in feed.items)
        with pytest.raises(ConsultationUnavailableError):
            read_consultation_detail(db, storage, consultation_id, owner_id, None)
        with pytest.raises(ConsultationUnavailableError):
            read_consultation_photo(db, storage, consultation_id, photo_id, reader_id, None)
        with pytest.raises(ConsultationUnavailableError):
            submit_vote(db, consultation_id, reader_id, None, photo_id)
