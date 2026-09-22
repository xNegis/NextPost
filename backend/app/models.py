import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

EMAIL_MAX_LENGTH = 320
ALIAS_MAX_LENGTH = 30

STORAGE_KEY_MAX_LENGTH = 64
DELETION_ERROR_MAX_LENGTH = 200


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("email", name="uq_accounts_email"),
        UniqueConstraint("alias_canonical", name="uq_accounts_alias_canonical"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), nullable=False)
    alias: Mapped[str] = mapped_column(String(ALIAS_MAX_LENGTH), nullable=False)
    alias_canonical: Mapped[str] = mapped_column(String(ALIAS_MAX_LENGTH), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PhotoUploadSessionState(str, enum.Enum):
    active = "active"
    discarded = "discarded"
    abandoned = "abandoned"


class PhotoImageState(str, enum.Enum):
    pending = "pending"
    ready = "ready"
    failed = "failed"
    revoked = "revoked"
    deleted = "deleted"


class PhotoUploadSession(Base):
    __tablename__ = "photo_upload_sessions"
    __table_args__ = (
        Index("ix_photo_upload_sessions_account_id", "account_id"),
        Index("ix_photo_upload_sessions_state_lease", "state", "lease_expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[PhotoUploadSessionState] = mapped_column(
        Enum(PhotoUploadSessionState, native_enum=False, length=16), nullable=False
    )
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    discarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PhotoUploadImage(Base):
    __tablename__ = "photo_upload_images"
    __table_args__ = (
        UniqueConstraint(
            "upload_session_id", "attempt_id", name="uq_photo_upload_images_session_attempt"
        ),
        Index("ix_photo_upload_images_session_id", "upload_session_id"),
        Index("ix_photo_upload_images_deletion", "state", "deletion_requested_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    upload_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("photo_upload_sessions.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    state: Mapped[PhotoImageState] = mapped_column(
        Enum(PhotoImageState, native_enum=False, length=16), nullable=False
    )
    storage_key: Mapped[str | None] = mapped_column(String(STORAGE_KEY_MAX_LENGTH), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    byte_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deletion_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deletion_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_deletion_error: Mapped[str | None] = mapped_column(
        String(DELETION_ERROR_MAX_LENGTH), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
