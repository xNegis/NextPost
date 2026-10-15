import uuid
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.photos import get_photo_storage
from app.auth import get_current_account
from app.config import get_settings
from app.consultation_service import (
    ConsultationCapReachedError,
    ConsultationConflictError,
    ConsultationUnavailableError,
    LinkConflictError,
    MyConsultationFinalizedDetail,
    MyConsultationFinalizedItem,
    MyConsultationOpenItem,
    NotPrivateError,
    decode_cursor,
    decode_feed_cursor,
    get_open_capacity,
    list_feed,
    list_my_consultations,
    mutate_link,
    publish_consultation,
    read_consultation_detail,
    read_consultation_photo,
    read_my_consultation,
    read_owner_link,
)
from app.db import get_db_session
from app.models import Account
from app.photo_service import InactiveSessionError, NotFoundError, PublicationInvalidError
from app.schemas import (
    ConsultationCapacityResponse,
    ConsultationDetailResponse,
    ConsultationPhotoResponse,
    ConsultationPublishedResponse,
    ConsultationPublishRequest,
    FeedItemResponse,
    FeedPhotoResponse,
    FeedResponse,
    LinkMutationRequest,
    MyConsultationFinalizedListItem,
    MyConsultationListResponse,
    MyConsultationOpenDetail,
    MyConsultationOpenListItem,
    MyConsultationOwnerDetail,
    OwnerLinkResponse,
)
from app.schemas import (
    MyConsultationFinalizedDetail as MyConsultationFinalizedDetailSchema,
)
from app.storage import PhotoStorage

router = APIRouter(tags=["consultations"])

PRIVATE_LINK_HEADER = "X-NextPost-Private-Link"


def require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is None:
        return
    if origin not in get_settings().cors_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"code": "origin_not_allowed"}
        )


def _published_at_iso(value) -> str:
    return value.isoformat() + "Z"


def _private_link_token(header: str | None) -> str | None:
    if header is None or header == "":
        return None
    return header


def _set_private_read_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"


def _detail_response(detail) -> ConsultationDetailResponse:
    return ConsultationDetailResponse(
        id=detail.id,
        owner_nickname=detail.owner_nickname,
        question=detail.question,
        context=detail.context,
        audience=detail.audience,
        state=detail.state,
        published_at=_published_at_iso(detail.published_at),
        photos=[
            ConsultationPhotoResponse(id=photo.id, width=photo.width, height=photo.height)
            for photo in detail.photos
        ],
    )


@router.get(
    "/my-consultations",
    response_model=MyConsultationListResponse,
)
def my_consultations(
    state: Literal["open", "finalized"] = "open",
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    response: Response = Response(),
) -> MyConsultationListResponse:
    _set_private_read_headers(response)

    cursor_key = None
    if cursor is not None:
        decoded = decode_cursor(cursor)
        if decoded is None or decoded[0] != state:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation_error",
                    "field_errors": {"cursor": "Enter a valid page cursor."},
                },
            )
        cursor_key = (decoded[1], decoded[2])

    result = list_my_consultations(db, account.id, state, limit, cursor_key)

    items: list[MyConsultationOpenListItem | MyConsultationFinalizedListItem] = []
    for item in result.items:
        if isinstance(item, MyConsultationOpenItem):
            items.append(
                MyConsultationOpenListItem(
                    id=item.id,
                    state="open",
                    question=item.question,
                    audience=item.audience,
                    published_at=_published_at_iso(item.published_at),
                )
            )
        else:
            assert isinstance(item, MyConsultationFinalizedItem)
            items.append(
                MyConsultationFinalizedListItem(
                    id=item.id,
                    state="finalized",
                    published_at=_published_at_iso(item.published_at),
                )
            )

    return MyConsultationListResponse(items=items, next_cursor=result.next_cursor)


@router.get(
    "/my-consultations/{consultation_id}",
    response_model=MyConsultationOwnerDetail,
)
def my_consultation_detail(
    consultation_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    response: Response = Response(),
) -> MyConsultationOpenDetail | MyConsultationFinalizedDetailSchema:
    _set_private_read_headers(response)

    try:
        detail = read_my_consultation(db, consultation_id, account.id)
    except ConsultationUnavailableError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    if isinstance(detail, MyConsultationFinalizedDetail):
        return MyConsultationFinalizedDetailSchema(
            id=detail.id,
            state="finalized",
            published_at=_published_at_iso(detail.published_at),
        )

    return MyConsultationOpenDetail(
        id=detail.id,
        state="open",
        owner_nickname=detail.owner_nickname,
        question=detail.question,
        context=detail.context,
        audience=detail.audience,
        published_at=_published_at_iso(detail.published_at),
        photos=[
            ConsultationPhotoResponse(id=photo.id, width=photo.width, height=photo.height)
            for photo in detail.photos
        ],
    )


@router.get(
    "/consultation-capacity",
    response_model=ConsultationCapacityResponse,
)
def consultation_capacity(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> ConsultationCapacityResponse:
    capacity = get_open_capacity(db, account.id)
    return ConsultationCapacityResponse(
        open_count=capacity.open_count,
        limit=capacity.limit,
        can_start=capacity.can_start,
    )


@router.post(
    "/consultations",
    response_model=ConsultationPublishedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_consultation(
    payload: ConsultationPublishRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    storage: PhotoStorage = Depends(get_photo_storage),
    _origin: None = Depends(require_trusted_origin),
) -> ConsultationPublishedResponse:
    try:
        consultation = publish_consultation(
            db,
            storage,
            account.id,
            payload.session_id,
            payload.ordered_image_ids,
            payload.question,
            payload.context,
            payload.audience,
        )
    except ConsultationConflictError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    except ConsultationCapReachedError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc
    except InactiveSessionError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    except PublicationInvalidError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc

    return ConsultationPublishedResponse(
        id=str(consultation.id),
        state=cast(Literal["open"], consultation.state.value),
        audience=consultation.audience,
    )


@router.get(
    "/consultations/feed",
    response_model=FeedResponse,
)
def consultation_feed(
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    response: Response = Response(),
) -> FeedResponse:
    _set_private_read_headers(response)

    cursor_key = None
    if cursor is not None:
        decoded = decode_feed_cursor(cursor)
        if decoded is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation_error",
                    "field_errors": {"cursor": "Enter a valid page cursor."},
                },
            )
        cursor_key = (decoded[0], decoded[1])

    result = list_feed(db, account.id, limit, cursor_key)

    items = [
        FeedItemResponse(
            id=item.id,
            owner_nickname=item.owner_nickname,
            question=item.question,
            context_excerpt=item.context_excerpt,
            audience="public",
            state="open",
            published_at=_published_at_iso(item.published_at),
            is_owner=item.is_owner,
            first_photo=FeedPhotoResponse(
                id=item.first_photo.id,
                width=item.first_photo.width,
                height=item.first_photo.height,
            ),
        )
        for item in result.items
    ]
    return FeedResponse(items=items, next_cursor=result.next_cursor)


@router.get(
    "/consultations/{consultation_id}",
    response_model=ConsultationDetailResponse,
)
def consultation_detail(
    consultation_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    storage: PhotoStorage = Depends(get_photo_storage),
    private_link: Annotated[str | None, Header(alias=PRIVATE_LINK_HEADER)] = None,
    response: Response = Response(),
) -> ConsultationDetailResponse:
    _set_private_read_headers(response)
    try:
        detail = read_consultation_detail(
            db, storage, consultation_id, account.id, _private_link_token(private_link)
        )
    except ConsultationUnavailableError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc
    return _detail_response(detail)


@router.get("/consultations/{consultation_id}/photos/{photo_id}/content")
def consultation_photo_content(
    consultation_id: uuid.UUID,
    photo_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    storage: PhotoStorage = Depends(get_photo_storage),
    private_link: Annotated[str | None, Header(alias=PRIVATE_LINK_HEADER)] = None,
) -> Response:
    try:
        content, content_type = read_consultation_photo(
            db, storage, consultation_id, photo_id, account.id, _private_link_token(private_link)
        )
    except ConsultationUnavailableError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.get(
    "/consultations/{consultation_id}/private-link",
    response_model=OwnerLinkResponse,
)
def consultation_private_link(
    consultation_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> OwnerLinkResponse:
    try:
        link = read_owner_link(db, consultation_id, account.id)
    except ConsultationUnavailableError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc
    except NotPrivateError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    return OwnerLinkResponse(active=link.active, generation=link.generation, token=link.token)


def _mutate_link(
    operation: str,
    consultation_id: uuid.UUID,
    payload: LinkMutationRequest,
    account: Account,
    db: Session,
) -> OwnerLinkResponse:
    try:
        link = mutate_link(db, consultation_id, account.id, operation, payload.expected_generation)
    except ConsultationUnavailableError as exc:
        raise HTTPException(status_code=404, detail={"code": exc.code}) from exc
    except NotPrivateError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    except LinkConflictError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code}) from exc
    return OwnerLinkResponse(active=link.active, generation=link.generation, token=link.token)


@router.post(
    "/consultations/{consultation_id}/private-link/disable",
    response_model=OwnerLinkResponse,
)
def disable_private_link(
    consultation_id: uuid.UUID,
    payload: LinkMutationRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    _origin: None = Depends(require_trusted_origin),
) -> OwnerLinkResponse:
    return _mutate_link("disable", consultation_id, payload, account, db)


@router.post(
    "/consultations/{consultation_id}/private-link/replace",
    response_model=OwnerLinkResponse,
)
def replace_private_link(
    consultation_id: uuid.UUID,
    payload: LinkMutationRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    _origin: None = Depends(require_trusted_origin),
) -> OwnerLinkResponse:
    return _mutate_link("replace", consultation_id, payload, account, db)


@router.post(
    "/consultations/{consultation_id}/private-link/create",
    response_model=OwnerLinkResponse,
)
def create_private_link(
    consultation_id: uuid.UUID,
    payload: LinkMutationRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    _origin: None = Depends(require_trusted_origin),
) -> OwnerLinkResponse:
    return _mutate_link("create", consultation_id, payload, account, db)
