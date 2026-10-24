import uuid
from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_account
from app.config import get_settings
from app.db import get_db_session
from app.models import Account
from app.photo_service import (
    InvalidAttemptError,
    _as_naive_utc,
    create_upload_session,
    discard_upload_session,
    read_image,
    remove_image,
    renew_upload_session,
    upload_image,
)
from app.schemas import (
    ApplicationConfigResponse,
    UploadImageResponse,
    UploadSessionResponse,
)
from app.storage import PhotoStorage, build_photo_storage

router = APIRouter(tags=["photos"])


@lru_cache(maxsize=1)
def _photo_storage() -> PhotoStorage:
    return build_photo_storage(get_settings())


def get_photo_storage() -> PhotoStorage:
    return _photo_storage()


def _lease_iso(expires_at: datetime) -> str:
    return _as_naive_utc(expires_at).isoformat() + "Z"


@router.get("/application-config", response_model=ApplicationConfigResponse)
def application_config(
    _account: Account = Depends(get_current_account),
) -> ApplicationConfigResponse:
    settings = get_settings()
    return ApplicationConfigResponse(
        consultation_min_photos=settings.consultation_min_photos,
        consultation_max_photos=settings.consultation_max_photos,
        max_open_consultations=settings.max_open_consultations,
        photo_max_input_bytes=settings.photo_max_input_bytes,
        consultation_question_max_length=settings.consultation_question_max_length,
        consultation_context_max_length=settings.consultation_context_max_length,
    )


@router.post(
    "/photo-upload-sessions",
    response_model=UploadSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> UploadSessionResponse:
    row = create_upload_session(db, account.id)
    return UploadSessionResponse(id=str(row.id), lease_expires_at=_lease_iso(row.lease_expires_at))


@router.post(
    "/photo-upload-sessions/{session_id}/lease",
    response_model=UploadSessionResponse,
)
def renew_session(
    session_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> UploadSessionResponse:
    row = renew_upload_session(db, account.id, session_id)
    return UploadSessionResponse(id=str(row.id), lease_expires_at=_lease_iso(row.lease_expires_at))


@router.post(
    "/photo-upload-sessions/{session_id}/images",
    response_model=UploadImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_session_image(
    session_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    storage: PhotoStorage = Depends(get_photo_storage),
    file: UploadFile = File(...),
    attempt_id: str = Form(...),
) -> UploadImageResponse:
    try:
        attempt_uuid = uuid.UUID(attempt_id)
    except (TypeError, ValueError) as exc:
        raise InvalidAttemptError() from exc

    result = upload_image(db, storage, account.id, session_id, attempt_uuid, file.file)
    return UploadImageResponse(id=str(result.id), width=result.width, height=result.height)


@router.get("/photo-upload-sessions/{session_id}/images/{image_id}/content")
def read_session_image(
    session_id: uuid.UUID,
    image_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
    storage: PhotoStorage = Depends(get_photo_storage),
) -> Response:
    content, content_type = read_image(db, storage, account.id, session_id, image_id)
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/photo-upload-sessions/{session_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session_image(
    session_id: uuid.UUID,
    image_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> Response:
    remove_image(db, account.id, session_id, image_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/photo-upload-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session),
) -> Response:
    discard_upload_session(db, account.id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
