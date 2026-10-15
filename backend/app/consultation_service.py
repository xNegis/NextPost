"""Consultation persistence, atomic publication, protected reads and owner link management (RF-10).

This module owns the durable consultation lifecycle that RF-09's pure audience/access/link rules
did not persist. It reuses ``PhotoUploadImage`` as the single private-file ledger and promotes
selected images by creating ``ConsultationPhoto`` associations over the same bytes, so publication
is a single relational transaction with no filesystem move.

Lock order for publication and future slot-releasing actions is documented here and followed by
every writer: author/account row, then upload session, then photos. Link mutations lock the
consultation row. Protected reads load current committed state on every request.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, cast

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.audience import PRIVATE, PUBLIC, Audience, validate_audience
from app.config import get_settings
from app.consultation_access import (
    AccessOperation,
    AccessSnapshot,
    ConsultationLifecycle,
    can_access,
)
from app.consultation_text import validate_consultation_text
from app.models import (
    Account,
    Consultation,
    ConsultationPhoto,
    ConsultationState,
    PhotoImageState,
    PhotoUploadImage,
    PhotoUploadSession,
    PhotoUploadSessionState,
)
from app.photo_service import (
    ImageUnavailableError,
    InactiveSessionError,
    NotFoundError,
    PublicationInvalidError,
    _as_naive_utc,
    _is_expired,
    utcnow,
)
from app.private_link import (
    PrivateLinkState,
    create_new_link,
    current_link_token,
    disable_link,
    parse_generation,
    replace_link,
    verify_current_link,
)
from app.storage import PhotoStorage, StorageError

logger = logging.getLogger(__name__)

_FINGERPRINT_VERSION = "v1"


class ConsultationError(Exception):
    code = "consultation_error"
    status_code = 400

    def __init__(self) -> None:
        super().__init__(self.code)


class ConsultationUnavailableError(ConsultationError):
    code = "consultation_unavailable"
    status_code = 404


class ConsultationCapReachedError(ConsultationError):
    code = "max_open_consultations_reached"
    status_code = 409


class ConsultationConflictError(ConsultationError):
    code = "consultation_conflict"
    status_code = 409


class NotPrivateError(ConsultationError):
    code = "not_private"
    status_code = 409


class LinkConflictError(ConsultationError):
    code = "link_conflict"
    status_code = 409


class FeedUnavailableError(ConsultationError):
    code = "unavailable"
    status_code = 503


@dataclass(frozen=True)
class OpenCapacity:
    open_count: int
    limit: int
    can_start: bool


@dataclass(frozen=True)
class ConsultationPhotoDetail:
    id: str
    width: int
    height: int


@dataclass(frozen=True)
class ConsultationDetail:
    id: str
    owner_nickname: str
    question: str
    context: str | None
    audience: str
    state: Literal["open"]
    published_at: datetime
    photos: list[ConsultationPhotoDetail]


@dataclass(frozen=True)
class OwnerLinkState:
    active: bool
    generation: str
    token: str | None


@dataclass(frozen=True)
class MyConsultationOpenItem:
    id: str
    state: Literal["open"]
    question: str
    audience: str
    published_at: datetime


@dataclass(frozen=True)
class MyConsultationFinalizedItem:
    id: str
    state: Literal["finalized"]
    published_at: datetime


@dataclass(frozen=True)
class MyConsultationListResult:
    items: list[MyConsultationOpenItem | MyConsultationFinalizedItem]
    next_cursor: str | None


@dataclass(frozen=True)
class MyConsultationFinalizedDetail:
    id: str
    state: Literal["finalized"]
    published_at: datetime


@dataclass(frozen=True)
class FeedPhoto:
    id: str
    width: int
    height: int


@dataclass(frozen=True)
class FeedItem:
    id: str
    owner_nickname: str
    question: str
    context_excerpt: str | None
    audience: Literal["public"]
    state: Literal["open"]
    published_at: datetime
    is_owner: bool
    first_photo: FeedPhoto


@dataclass(frozen=True)
class FeedResult:
    items: list[FeedItem]
    next_cursor: str | None


_CURSOR_VERSION = "v1"
_CURSOR_MAX_LENGTH = 512
_CURSOR_STATES = ("open", "finalized")


def encode_cursor(state: str, published_at: datetime, consultation_id: uuid.UUID) -> str:
    """Encode a bounded URL-safe pagination cursor over ``(published_at, id)``."""
    payload = json.dumps(
        [_CURSOR_VERSION, state, _as_naive_utc(published_at).isoformat(), str(consultation_id)],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(raw: str) -> tuple[str, datetime, uuid.UUID] | None:
    """Decode and strictly validate a cursor; return ``None`` for malformed input."""
    if not isinstance(raw, str) or raw == "" or len(raw) > _CURSOR_MAX_LENGTH:
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        parsed = json.loads(decoded)
    except Exception:
        return None
    if not isinstance(parsed, list) or len(parsed) != 4:
        return None
    version, state, timestamp, consultation_id = parsed
    if version != _CURSOR_VERSION:
        return None
    if state not in _CURSOR_STATES:
        return None
    if not isinstance(timestamp, str) or not isinstance(consultation_id, str):
        return None
    try:
        published_at = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    if published_at.tzinfo is not None:
        return None
    try:
        cid = uuid.UUID(consultation_id)
    except (TypeError, ValueError):
        return None
    return state, published_at, cid


_FEED_CURSOR_VERSION = "feed-v1"
_FEED_CURSOR_MAX_LENGTH = 512
_FEED_CONTEXT_EXCERPT_CODEPOINTS = 160


def encode_feed_cursor(published_at: datetime, consultation_id: uuid.UUID) -> str:
    """Encode a bounded URL-safe feed pagination cursor over ``(published_at, id)``."""
    payload = json.dumps(
        [
            _FEED_CURSOR_VERSION,
            _as_naive_utc(published_at).isoformat(),
            str(consultation_id),
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")


def decode_feed_cursor(raw: str) -> tuple[datetime, uuid.UUID] | None:
    """Decode and strictly validate a feed cursor; return ``None`` for malformed input.

    The feed cursor carries exactly version ``feed-v1`` and a UTC publication timestamp plus a
    canonical UUID. Owner-list cursors (version ``v1``) and any other tuple shape are rejected.
    """
    if not isinstance(raw, str) or raw == "" or len(raw) > _FEED_CURSOR_MAX_LENGTH:
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        parsed = json.loads(decoded)
    except Exception:
        return None
    if not isinstance(parsed, list) or len(parsed) != 3:
        return None
    version, timestamp, consultation_id = parsed
    if version != _FEED_CURSOR_VERSION:
        return None
    if not isinstance(timestamp, str) or not isinstance(consultation_id, str):
        return None
    try:
        published_at = datetime.fromisoformat(timestamp)
    except ValueError:
        return None
    if published_at.tzinfo is not None:
        return None
    try:
        cid = uuid.UUID(consultation_id)
    except (TypeError, ValueError):
        return None
    return published_at, cid


def _context_excerpt(context: str | None) -> str | None:
    if context is None:
        return None
    if len(context) <= _FEED_CONTEXT_EXCERPT_CODEPOINTS:
        return context
    return context[:_FEED_CONTEXT_EXCERPT_CODEPOINTS] + "…"


def fingerprint(
    ordered_image_ids: list[uuid.UUID], question: str, context: str | None, audience: str
) -> str:
    """Return a versioned digest over the canonical publication payload."""
    payload = json.dumps(
        [
            _FINGERPRINT_VERSION,
            [str(image_id) for image_id in ordered_image_ids],
            question,
            context,
            audience,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _lock_account(db: Session, account_id: uuid.UUID) -> None:
    db.execute(
        select(Account.id).where(Account.id == account_id).with_for_update()
    ).scalar_one_or_none()


def _lock_session(db: Session, account_id: uuid.UUID, session_id: uuid.UUID) -> PhotoUploadSession:
    row = db.execute(
        select(PhotoUploadSession).where(PhotoUploadSession.id == session_id).with_for_update()
    ).scalar_one_or_none()
    if row is None or row.account_id != account_id:
        raise NotFoundError()
    return row


def _lock_and_validate_images(
    db: Session, storage: PhotoStorage, session_id: uuid.UUID, ordered_ids: list[uuid.UUID]
) -> list[PhotoUploadImage]:
    settings = get_settings()
    if len(ordered_ids) != len(set(ordered_ids)):
        raise PublicationInvalidError()
    if not (
        settings.consultation_min_photos <= len(ordered_ids) <= settings.consultation_max_photos
    ):
        raise PublicationInvalidError()

    images: list[PhotoUploadImage] = []
    for image_id in ordered_ids:
        row = db.execute(
            select(PhotoUploadImage).where(PhotoUploadImage.id == image_id).with_for_update()
        ).scalar_one_or_none()
        if row is None or row.upload_session_id != session_id:
            raise NotFoundError()
        if row.state != PhotoImageState.ready or row.storage_key is None:
            raise PublicationInvalidError()
        if not storage.exists(row.storage_key):
            logger.error(
                "publication photo bytes are missing: image_id=%s session_id=%s",
                row.id,
                session_id,
            )
            raise PublicationInvalidError()
        images.append(row)
    return images


def _revoke_unselected(
    db: Session, session_id: uuid.UUID, selected_ids: set[uuid.UUID], now: datetime
) -> int:
    statement = select(PhotoUploadImage).where(
        PhotoUploadImage.upload_session_id == session_id,
        PhotoUploadImage.state.in_((PhotoImageState.ready, PhotoImageState.pending)),
    )
    if selected_ids:
        statement = statement.where(PhotoUploadImage.id.not_in(selected_ids))
    rows = db.scalars(statement).all()
    for row in rows:
        row.state = PhotoImageState.revoked
        row.deletion_requested_at = now
        row.deletion_completed_at = None
    return len(rows)


def publish_consultation(
    db: Session,
    storage: PhotoStorage,
    account_id: uuid.UUID,
    session_id: uuid.UUID,
    ordered_image_ids: list[uuid.UUID],
    question: str,
    context: str | None,
    audience: Audience,
    now: datetime | None = None,
) -> Consultation:
    settings = get_settings()
    current = now or utcnow()
    normalized_text, text_errors = validate_consultation_text(
        question,
        context,
        question_max=settings.consultation_question_max_length,
        context_max=settings.consultation_context_max_length,
    )
    normalized_audience, audience_error = validate_audience(audience)
    if text_errors or audience_error is not None:
        raise PublicationInvalidError()
    assert normalized_text is not None
    assert normalized_audience is not None

    question = normalized_text.question
    context = normalized_text.context
    audience = normalized_audience
    payload_fingerprint = fingerprint(ordered_image_ids, question, context, audience)

    # Serialize publications for this author so the open cap cannot be exceeded under
    # concurrency. This lock also works when the author has zero consultations.
    _lock_account(db, account_id)

    session_row = _lock_session(db, account_id, session_id)

    # Idempotent retry: one consultation per source upload session, resolved before any
    # new-publication lease/cap/limit rejection so a lost response never duplicates.
    existing = db.scalar(select(Consultation).where(Consultation.source_session_id == session_id))
    if existing is not None:
        if existing.owner_id == account_id and existing.fingerprint == payload_fingerprint:
            return existing
        raise ConsultationConflictError()

    if session_row.state != PhotoUploadSessionState.active or _is_expired(
        session_row.lease_expires_at, current
    ):
        raise InactiveSessionError()

    images = _lock_and_validate_images(db, storage, session_id, ordered_image_ids)

    open_count = db.scalar(
        select(func.count())
        .select_from(Consultation)
        .where(
            Consultation.owner_id == account_id,
            Consultation.state == ConsultationState.open,
        )
    )
    if open_count is not None and open_count >= settings.max_open_consultations:
        raise ConsultationCapReachedError()

    is_private = audience == PRIVATE
    consultation = Consultation(
        owner_id=account_id,
        question=question,
        context=context,
        audience=audience,
        state=ConsultationState.open,
        published_at=current,
        source_session_id=session_id,
        fingerprint=payload_fingerprint,
        private_link_generation=1 if is_private else 0,
        private_link_active=is_private,
    )
    db.add(consultation)
    db.flush()

    for ordinal, image in enumerate(images):
        db.add(
            ConsultationPhoto(consultation_id=consultation.id, image_id=image.id, ordinal=ordinal)
        )

    selected_ids = {image.id for image in images}
    _revoke_unselected(db, session_id, selected_ids, current)

    session_row.state = PhotoUploadSessionState.consumed
    session_row.lease_expires_at = current

    db.commit()
    return consultation


def get_open_capacity(db: Session, account_id: uuid.UUID) -> OpenCapacity:
    settings = get_settings()
    open_count = db.scalar(
        select(func.count())
        .select_from(Consultation)
        .where(
            Consultation.owner_id == account_id,
            Consultation.state == ConsultationState.open,
        )
    )
    count = int(open_count or 0)
    return OpenCapacity(
        open_count=count,
        limit=settings.max_open_consultations,
        can_start=count < settings.max_open_consultations,
    )


def _build_snapshot(consultation: Consultation) -> AccessSnapshot:
    return AccessSnapshot(
        consultation_id=str(consultation.id),
        owner_id=str(consultation.owner_id),
        audience=cast(Audience, consultation.audience),
        lifecycle=ConsultationLifecycle(consultation.state.value),
        private_link_active=bool(consultation.private_link_active),
        private_link_generation=int(consultation.private_link_generation),
    )


def _link_verifier(secret: str):
    def verify(state: PrivateLinkState, token: str | None) -> bool:
        return verify_current_link(state, token, secret)

    return verify


def _authorize(
    consultation: Consultation, account_id: uuid.UUID, presented_token: str | None
) -> AccessSnapshot:
    snapshot = _build_snapshot(consultation)
    decision = can_access(
        snapshot,
        str(account_id),
        presented_token,
        AccessOperation.read,
        _link_verifier(get_settings().private_link_secret),
    )
    if not decision.allowed:
        raise ConsultationUnavailableError()
    return snapshot


def _build_open_detail(db: Session, consultation: Consultation) -> ConsultationDetail:
    owner = db.get(Account, consultation.owner_id)
    nickname = owner.alias if owner is not None else ""

    photo_rows = db.scalars(
        select(ConsultationPhoto)
        .where(ConsultationPhoto.consultation_id == consultation.id)
        .order_by(ConsultationPhoto.ordinal)
    ).all()

    photos: list[ConsultationPhotoDetail] = []
    for photo in photo_rows:
        image = db.get(PhotoUploadImage, photo.image_id)
        photos.append(
            ConsultationPhotoDetail(
                id=str(photo.id),
                width=image.width if image is not None and image.width is not None else 0,
                height=image.height if image is not None and image.height is not None else 0,
            )
        )

    return ConsultationDetail(
        id=str(consultation.id),
        owner_nickname=nickname,
        question=consultation.question,
        context=consultation.context,
        audience=consultation.audience,
        state=cast(Literal["open"], consultation.state.value),
        published_at=_as_naive_utc(consultation.published_at),
        photos=photos,
    )


def read_consultation_detail(
    db: Session,
    storage: PhotoStorage,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    presented_token: str | None,
) -> ConsultationDetail:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ConsultationUnavailableError()
    _authorize(consultation, account_id, presented_token)
    return _build_open_detail(db, consultation)


def read_my_consultation(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
) -> ConsultationDetail | MyConsultationFinalizedDetail:
    """Return the owner-only management projection for a single consultation.

    Ownership is checked before any open projection is reused, so a Public reader or valid
    Private-link holder can never reach someone else's management view. Only the minimal
    ``id``/``owner_id``/``state``/``published_at`` columns are selected first; the full stored
    content is loaded only after the row is proven to belong to the account and to be ``open``.
    ``finalized`` returns only ``id``/``state``/``published_at`` with no content, storage or link
    work; every other lifecycle value is the generic unavailable result.
    """
    row = db.execute(
        select(
            Consultation.id,
            Consultation.owner_id,
            Consultation.state,
            Consultation.published_at,
        ).where(Consultation.id == consultation_id)
    ).first()
    if row is None or row.owner_id != account_id:
        raise ConsultationUnavailableError()
    if row.state == ConsultationState.open:
        consultation = db.get(Consultation, consultation_id)
        if consultation is None:
            raise ConsultationUnavailableError()
        return _build_open_detail(db, consultation)
    if row.state == ConsultationState.finalized:
        return MyConsultationFinalizedDetail(
            id=str(row.id),
            state="finalized",
            published_at=_as_naive_utc(row.published_at),
        )
    raise ConsultationUnavailableError()


def list_my_consultations(
    db: Session,
    account_id: uuid.UUID,
    state: Literal["open", "finalized"],
    limit: int,
    cursor: tuple[datetime, uuid.UUID] | None,
) -> MyConsultationListResult:
    """List the current owner's consultations in one canonical lifecycle state.

    Rows are scoped to the authenticated account in SQL (never client filtering) and ordered by
    ``published_at DESC, id DESC``. ``limit + 1`` rows are fetched to derive ``next_cursor``; the
    cursor is only pagination and carries no owner/token/authorization field.
    """
    lifecycle = ConsultationState.open if state == "open" else ConsultationState.finalized
    statement: Select[Any]
    if state == "open":
        statement = select(
            Consultation.id,
            Consultation.question,
            Consultation.audience,
            Consultation.published_at,
        ).where(
            Consultation.owner_id == account_id,
            Consultation.state == lifecycle,
        )
    else:
        statement = select(
            Consultation.id,
            Consultation.published_at,
        ).where(
            Consultation.owner_id == account_id,
            Consultation.state == lifecycle,
        )
    if cursor is not None:
        cursor_published_at, cursor_id = cursor
        statement = statement.where(
            or_(
                Consultation.published_at < cursor_published_at,
                and_(
                    Consultation.published_at == cursor_published_at,
                    Consultation.id < cursor_id,
                ),
            )
        )
    statement = statement.order_by(Consultation.published_at.desc(), Consultation.id.desc()).limit(
        limit + 1
    )
    rows = db.execute(statement).all()

    items: list[MyConsultationOpenItem | MyConsultationFinalizedItem] = []
    page_rows = rows[:limit]
    for row in page_rows:
        if state == "open":
            items.append(
                MyConsultationOpenItem(
                    id=str(row.id),
                    state="open",
                    question=row.question,
                    audience=row.audience,
                    published_at=_as_naive_utc(row.published_at),
                )
            )
        else:
            items.append(
                MyConsultationFinalizedItem(
                    id=str(row.id),
                    state="finalized",
                    published_at=_as_naive_utc(row.published_at),
                )
            )

    next_cursor = None
    if len(rows) > limit and page_rows:
        last = page_rows[-1]
        next_cursor = encode_cursor(state, _as_naive_utc(last.published_at), last.id)
    return MyConsultationListResult(items=items, next_cursor=next_cursor)


def _first_feed_photos(
    db: Session, consultation_ids: list[uuid.UUID]
) -> dict[uuid.UUID, FeedPhoto]:
    """Return the lowest-ordinal published photo metadata for each consultation in one set query.

    A missing association or non-positive stored dimensions is corrupt data: the caller must fail
    the whole page as a retryable feed failure rather than substitute another photo or silently
    drop the row.
    """
    if not consultation_ids:
        return {}
    min_ordinal = (
        select(
            ConsultationPhoto.consultation_id.label("consultation_id"),
            func.min(ConsultationPhoto.ordinal).label("min_ordinal"),
        )
        .where(ConsultationPhoto.consultation_id.in_(consultation_ids))
        .group_by(ConsultationPhoto.consultation_id)
        .subquery()
    )
    rows = db.execute(
        select(
            ConsultationPhoto.consultation_id,
            ConsultationPhoto.id,
            PhotoUploadImage.width,
            PhotoUploadImage.height,
        )
        .join(
            min_ordinal,
            (ConsultationPhoto.consultation_id == min_ordinal.c.consultation_id)
            & (ConsultationPhoto.ordinal == min_ordinal.c.min_ordinal),
        )
        .join(PhotoUploadImage, PhotoUploadImage.id == ConsultationPhoto.image_id)
    ).all()

    result: dict[uuid.UUID, FeedPhoto] = {}
    for consultation_id, photo_id, width, height in rows:
        if width is None or height is None or width <= 0 or height <= 0:
            logger.error(
                "feed first-photo metadata is invalid: consultation_id=%s photo_id=%s",
                consultation_id,
                photo_id,
            )
            raise FeedUnavailableError()
        result[consultation_id] = FeedPhoto(id=str(photo_id), width=int(width), height=int(height))
    return result


def list_feed(
    db: Session,
    account_id: uuid.UUID,
    limit: int,
    cursor: tuple[datetime, uuid.UUID] | None,
) -> FeedResult:
    """List open Public consultations across all authors, newest first, including the current owner.

    Eligibility (``audience == public`` and ``state == open``) is applied in SQL before pagination,
    so Private, terminal and temporary upload-session rows never appear. ``is_owner`` is derived
    server-side from the authenticated account. Nicknames and first-photo metadata are loaded
    set-wise; there are no per-row detail or storage reads.
    """
    statement: Select[Any] = select(
        Consultation.id,
        Consultation.owner_id,
        Consultation.question,
        Consultation.context,
        Consultation.published_at,
    ).where(
        Consultation.audience == PUBLIC,
        Consultation.state == ConsultationState.open,
    )
    if cursor is not None:
        cursor_published_at, cursor_id = cursor
        statement = statement.where(
            or_(
                Consultation.published_at < cursor_published_at,
                and_(
                    Consultation.published_at == cursor_published_at,
                    Consultation.id < cursor_id,
                ),
            )
        )
    statement = statement.order_by(Consultation.published_at.desc(), Consultation.id.desc()).limit(
        limit + 1
    )
    rows = db.execute(statement).all()

    page_rows = rows[:limit]
    consultation_ids = [row.id for row in page_rows]
    owner_ids = {row.owner_id for row in page_rows}

    nicknames = {
        owner_id: alias
        for owner_id, alias in db.execute(
            select(Account.id, Account.alias).where(Account.id.in_(owner_ids))
        ).all()
    }
    first_photos = _first_feed_photos(db, consultation_ids)

    items: list[FeedItem] = []
    for row in page_rows:
        first_photo = first_photos.get(row.id)
        if first_photo is None:
            logger.error("feed consultation has no first photo: consultation_id=%s", row.id)
            raise FeedUnavailableError()
        items.append(
            FeedItem(
                id=str(row.id),
                owner_nickname=nicknames.get(row.owner_id, ""),
                question=row.question,
                context_excerpt=_context_excerpt(row.context),
                audience="public",
                state="open",
                published_at=_as_naive_utc(row.published_at),
                is_owner=row.owner_id == account_id,
                first_photo=first_photo,
            )
        )

    next_cursor = None
    if len(rows) > limit and page_rows:
        last = page_rows[-1]
        next_cursor = encode_feed_cursor(_as_naive_utc(last.published_at), last.id)
    return FeedResult(items=items, next_cursor=next_cursor)


def read_consultation_photo(
    db: Session,
    storage: PhotoStorage,
    consultation_id: uuid.UUID,
    photo_id: uuid.UUID,
    account_id: uuid.UUID,
    presented_token: str | None,
) -> tuple[bytes, str]:
    consultation = db.get(Consultation, consultation_id)
    if consultation is None:
        raise ConsultationUnavailableError()
    _authorize(consultation, account_id, presented_token)

    photo = db.scalar(
        select(ConsultationPhoto).where(
            ConsultationPhoto.id == photo_id,
            ConsultationPhoto.consultation_id == consultation_id,
        )
    )
    if photo is None:
        raise ConsultationUnavailableError()

    image = db.get(PhotoUploadImage, photo.image_id)
    if image is None or image.state != PhotoImageState.ready or image.storage_key is None:
        logger.error(
            "consultation photo is not ready: photo_id=%s consultation_id=%s",
            photo_id,
            consultation_id,
        )
        raise ImageUnavailableError()

    try:
        content = storage.read_normalized(image.storage_key)
    except StorageError:
        logger.error(
            "consultation photo bytes are missing: photo_id=%s consultation_id=%s",
            photo_id,
            consultation_id,
        )
        raise ImageUnavailableError() from None
    return content, "image/jpeg"


def read_owner_link(
    db: Session, consultation_id: uuid.UUID, account_id: uuid.UUID
) -> OwnerLinkState:
    consultation = db.get(Consultation, consultation_id)
    if (
        consultation is None
        or consultation.owner_id != account_id
        or consultation.state != ConsultationState.open
    ):
        raise ConsultationUnavailableError()
    if consultation.audience != PRIVATE:
        raise NotPrivateError()
    return _owner_link_state(consultation)


def mutate_link(
    db: Session,
    consultation_id: uuid.UUID,
    account_id: uuid.UUID,
    operation: str,
    expected_generation: str,
) -> OwnerLinkState:
    consultation = db.execute(
        select(Consultation).where(Consultation.id == consultation_id).with_for_update()
    ).scalar_one_or_none()
    if (
        consultation is None
        or consultation.owner_id != account_id
        or consultation.state != ConsultationState.open
    ):
        raise ConsultationUnavailableError()
    if consultation.audience != PRIVATE:
        raise NotPrivateError()

    expected = parse_generation(expected_generation)
    if expected is None:
        raise LinkConflictError()

    current_generation = int(consultation.private_link_generation)
    state = PrivateLinkState(
        str(consultation.id), current_generation, bool(consultation.private_link_active)
    )

    if operation == "disable":
        transition = disable_link(state, expected)
    elif operation == "replace":
        transition = replace_link(state, expected)
    elif operation == "create":
        transition = create_new_link(state, expected)
    else:
        raise LinkConflictError()

    if not transition.ok or transition.state is None:
        raise LinkConflictError()

    consultation.private_link_generation = transition.state.generation
    consultation.private_link_active = transition.state.active
    db.commit()
    return _owner_link_state(consultation)


def _owner_link_state(consultation: Consultation) -> OwnerLinkState:
    generation = int(consultation.private_link_generation)
    active = bool(consultation.private_link_active)
    token = None
    if active:
        token = current_link_token(
            PrivateLinkState(str(consultation.id), generation, True),
            get_settings().private_link_secret,
        )
    return OwnerLinkState(active=active, generation=str(generation), token=token)
