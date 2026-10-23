import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.consultation_finalization_service import (
    FinalizationDeclaration,
    finalize_consultation,
)
from app.db import Base
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
    list_participation_history,
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL not configured")

SNAPSHOT = datetime(2030, 1, 1, 0, 0, 0)


@pytest.fixture()
def pg_factory() -> sessionmaker[Session]:
    assert TEST_DATABASE_URL is not None
    engine = create_engine(TEST_DATABASE_URL, pool_size=20, max_overflow=0)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


def _account(db: Session, email: str, alias: str) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    account = Account(
        email=f"{email.split('@')[0]}{suffix}@{email.split('@')[1]}",
        alias=f"{alias}{suffix}",
        alias_canonical=f"{alias}{suffix}".lower(),
        password_hash="x",
    )
    db.add(account)
    db.commit()
    return account.id


def _consultation(
    db: Session, owner_id: uuid.UUID, *, audience: str = "public"
) -> tuple[uuid.UUID, list[uuid.UUID]]:
    session = PhotoUploadSession(
        account_id=owner_id,
        state=PhotoUploadSessionState.consumed,
        lease_expires_at=datetime(2030, 1, 1),
    )
    db.add(session)
    db.flush()
    consultation = Consultation(
        owner_id=owner_id,
        question="Q",
        context=None,
        audience=audience,
        state=ConsultationState.open,
        published_at=datetime(2026, 1, 1, 12, 0, 0),
        source_session_id=session.id,
        fingerprint=uuid.uuid4().hex[:32],
        private_link_generation=1 if audience == "private" else 0,
        private_link_active=audience == "private",
    )
    db.add(consultation)
    db.flush()
    photos: list[uuid.UUID] = []
    for ordinal in range(2):
        image = PhotoUploadImage(
            upload_session_id=session.id,
            attempt_id=uuid.uuid4(),
            state=PhotoImageState.ready,
            storage_key=f"k{uuid.uuid4().hex[:12]}",
            width=64,
            height=64,
        )
        db.add(image)
        db.flush()
        photo = ConsultationPhoto(
            consultation_id=consultation.id, image_id=image.id, ordinal=ordinal
        )
        db.add(photo)
        db.flush()
        photos.append(photo.id)
    db.commit()
    return consultation.id, photos


def _vote(
    db: Session,
    cid: uuid.UUID,
    voter_id: uuid.UUID,
    photo_id: uuid.UUID,
    created_at: datetime,
) -> None:
    db.add(
        Vote(
            consultation_id=cid,
            voter_id=voter_id,
            consultation_photo_id=photo_id,
            created_at=created_at,
        )
    )
    db.commit()


def test_mixed_history_orders_and_paginates_on_postgres(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")

        ids: list[str] = []
        for index in range(25):
            cid, photos = _consultation(db, owner_id)
            _vote(db, cid, voter_id, photos[0], datetime(2026, 1, 1, 0, 0, index))
            ids.append(str(cid))

        collected: list[str] = []
        cursor = None
        while True:
            page = list_participation_history(db, voter_id, 20, cursor, now=SNAPSHOT)
            collected.extend(item.consultation_id for item in page.items)
            if page.next_cursor is None:
                break
            cursor = decode_history_cursor(page.next_cursor)

    assert len(collected) == len(set(collected)) == 25
    assert set(collected) == set(ids)


def test_outcome_uses_finalization_timestamp_on_postgres(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photos = _consultation(db, owner_id)
        _vote(db, cid, voter_id, photos[0], datetime(2026, 1, 1, 12, 0, 0))
        finalize_consultation(
            db,
            cid,
            owner_id,
            uuid.uuid4(),
            FinalizationDeclaration(kind="selected", option_ids=(photos[0],)),
            now=datetime(2026, 4, 1, 12, 0, 0),
        )

        page = list_participation_history(db, voter_id, 20, None, now=SNAPSHOT)

    assert len(page.items) == 1
    assert page.items[0].status == "matched"
    assert page.items[0].event_kind == "finalized"
    assert page.items[0].event_at == datetime(2026, 4, 1, 12, 0, 0)
    assert page.items[0].can_view is False


def test_outcome_precedes_open_residual_vote_on_postgres(pg_factory) -> None:
    with pg_factory() as db:
        owner_id = _account(db, "owner@example.com", "Owner")
        voter_id = _account(db, "voter@example.com", "Voter")
        cid, photos = _consultation(db, owner_id)
        _vote(db, cid, voter_id, photos[0], datetime(2026, 2, 1, 12, 0, 0))
        db.add(
            ConsultationFinalization(
                consultation_id=cid,
                operation_id=uuid.uuid4(),
                payload_fingerprint=uuid.uuid4().hex,
                finalized_at=datetime(2026, 3, 1, 12, 0, 0),
                total_votes=1,
            )
        )
        db.add(
            ConsultationOutcome(
                consultation_id=cid,
                voter_id=voter_id,
                outcome=FinalizationOutcome.matched,
            )
        )
        db.commit()

        page = list_participation_history(db, voter_id, 20, None, now=SNAPSHOT)

    assert len(page.items) == 1
    assert page.items[0].status == "matched"
    assert page.items[0].event_kind == "finalized"
