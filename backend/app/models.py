import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.consultation_lifecycle import ConsultationLifecycle
from app.db import Base

EMAIL_MAX_LENGTH = 320
ALIAS_MAX_LENGTH = 30

STORAGE_KEY_MAX_LENGTH = 64
DELETION_ERROR_MAX_LENGTH = 200
FINGERPRINT_MAX_LENGTH = 64


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
    consumed = "consumed"


# Compatibility alias: the canonical consultation lifecycle lives in ``consultation_lifecycle``
# (RF-11). ``ConsultationState`` remains the name used by the ORM column so existing imports and
# the SQLAlchemy ``Enum`` mapping keep working without a second independent definition.
ConsultationState = ConsultationLifecycle


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


class Consultation(Base):
    __tablename__ = "consultations"
    __table_args__ = (
        Index("ix_consultations_owner_state_created", "owner_id", "state", "created_at"),
        CheckConstraint(
            "audience IN ('public', 'private')",
            name="ck_consultations_audience",
        ),
        CheckConstraint(
            "(audience = 'public' AND private_link_active = false) OR "
            "(audience = 'private' AND private_link_generation >= 1)",
            name="ck_consultations_audience_link",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str] = mapped_column(String(8), nullable=False)
    state: Mapped[ConsultationState] = mapped_column(
        Enum(ConsultationState, native_enum=False, length=16),
        nullable=False,
        default=ConsultationState.open,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("photo_upload_sessions.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    fingerprint: Mapped[str] = mapped_column(String(FINGERPRINT_MAX_LENGTH), nullable=False)
    private_link_generation: Mapped[int] = mapped_column(Numeric(20, 0), nullable=False, default=0)
    private_link_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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


class ConsultationPhoto(Base):
    __tablename__ = "consultation_photos"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id", "ordinal", name="uq_consultation_photos_consultation_ordinal"
        ),
        UniqueConstraint("image_id", name="uq_consultation_photos_image_id"),
        # Candidate key so a Vote can prove (via a composite foreign key) that its selected
        # option belongs to the same consultation it references.
        UniqueConstraint("consultation_id", "id", name="uq_consultation_photos_consultation_id"),
        Index("ix_consultation_photos_consultation_id", "consultation_id"),
        Index("ix_consultation_photos_image_id", "image_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("photo_upload_images.id", ondelete="RESTRICT"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("consultation_id", "voter_id", name="uq_votes_consultation_voter"),
        ForeignKeyConstraint(
            ["consultation_id", "consultation_photo_id"],
            ["consultation_photos.consultation_id", "consultation_photos.id"],
            name="fk_votes_consultation_photo",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_votes_consultation_photo",
            "consultation_id",
            "consultation_photo_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("consultations.id", ondelete="RESTRICT"), nullable=False
    )
    voter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    consultation_photo_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
