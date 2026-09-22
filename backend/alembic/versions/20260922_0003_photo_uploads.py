"""Add photo upload sessions and images.

Revision ID: 20260922_0003
Revises: 20260915_0002
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260922_0003"
down_revision: str | None = "20260915_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "photo_upload_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('active', 'discarded', 'abandoned')",
            name="ck_photo_upload_sessions_state",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_photo_upload_sessions_account_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_photo_upload_sessions_account_id",
        "photo_upload_sessions",
        ["account_id"],
    )
    op.create_index(
        "ix_photo_upload_sessions_state_lease",
        "photo_upload_sessions",
        ["state", "lease_expires_at"],
    )

    op.create_table(
        "photo_upload_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("upload_session_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("storage_key", sa.String(length=64), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("byte_length", sa.Integer(), nullable=True),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deletion_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_deletion_error", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'ready', 'failed', 'revoked', 'deleted')",
            name="ck_photo_upload_images_state",
        ),
        sa.ForeignKeyConstraint(
            ["upload_session_id"],
            ["photo_upload_sessions.id"],
            name="fk_photo_upload_images_upload_session_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "upload_session_id",
            "attempt_id",
            name="uq_photo_upload_images_session_attempt",
        ),
    )
    op.create_index(
        "ix_photo_upload_images_session_id",
        "photo_upload_images",
        ["upload_session_id"],
    )
    op.create_index(
        "ix_photo_upload_images_deletion",
        "photo_upload_images",
        ["state", "deletion_requested_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_photo_upload_images_deletion", table_name="photo_upload_images")
    op.drop_index("ix_photo_upload_images_session_id", table_name="photo_upload_images")
    op.drop_table("photo_upload_images")
    op.drop_index("ix_photo_upload_sessions_state_lease", table_name="photo_upload_sessions")
    op.drop_index("ix_photo_upload_sessions_account_id", table_name="photo_upload_sessions")
    op.drop_table("photo_upload_sessions")
