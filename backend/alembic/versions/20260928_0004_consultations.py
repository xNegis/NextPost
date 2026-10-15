"""Add consultations, ordered consultation photos and consumed upload-session state.

Revision ID: 20260928_0004
Revises: 20260922_0003
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260928_0004"
down_revision: str | None = "20260922_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extend the upload-session state domain so a session can be terminally consumed
    # by exactly one publication. The existing rows remain temporary.
    op.drop_constraint("ck_photo_upload_sessions_state", "photo_upload_sessions", type_="check")
    op.create_check_constraint(
        "ck_photo_upload_sessions_state",
        "photo_upload_sessions",
        "state IN ('active', 'discarded', 'abandoned', 'consumed')",
    )

    op.create_table(
        "consultations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("audience", sa.String(length=8), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_session_id", sa.Uuid(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("private_link_generation", sa.Numeric(precision=20, scale=0), nullable=False),
        sa.Column("private_link_active", sa.Boolean(), nullable=False),
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
            "state IN ('open', 'finalized', 'deleted', 'removed')",
            name="ck_consultations_state",
        ),
        sa.CheckConstraint(
            "audience IN ('public', 'private')",
            name="ck_consultations_audience",
        ),
        sa.CheckConstraint(
            "(audience = 'public' AND private_link_active = false) OR "
            "(audience = 'private' AND private_link_generation >= 1)",
            name="ck_consultations_audience_link",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["accounts.id"],
            name="fk_consultations_owner_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_session_id"],
            ["photo_upload_sessions.id"],
            name="fk_consultations_source_session_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_session_id", name="uq_consultations_source_session_id"),
    )
    op.create_index(
        "ix_consultations_owner_state_created",
        "consultations",
        ["owner_id", "state", "created_at"],
    )

    op.create_table(
        "consultation_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            name="fk_consultation_photos_consultation_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["photo_upload_images.id"],
            name="fk_consultation_photos_image_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            "ordinal",
            name="uq_consultation_photos_consultation_ordinal",
        ),
        sa.UniqueConstraint("image_id", name="uq_consultation_photos_image_id"),
    )
    op.create_index(
        "ix_consultation_photos_consultation_id",
        "consultation_photos",
        ["consultation_id"],
    )
    op.create_index(
        "ix_consultation_photos_image_id",
        "consultation_photos",
        ["image_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    consultation_count = bind.execute(sa.text("SELECT count(*) FROM consultations")).scalar_one()
    consumed_session_count = bind.execute(
        sa.text("SELECT count(*) FROM photo_upload_sessions WHERE state = 'consumed'")
    ).scalar_one()
    if consultation_count or consumed_session_count:
        raise RuntimeError(
            "RF-10 downgrade refused: published consultations or consumed upload sessions exist"
        )

    op.drop_index("ix_consultation_photos_image_id", table_name="consultation_photos")
    op.drop_index("ix_consultation_photos_consultation_id", table_name="consultation_photos")
    op.drop_table("consultation_photos")
    op.drop_index("ix_consultations_owner_state_created", table_name="consultations")
    op.drop_table("consultations")
    op.drop_constraint("ck_photo_upload_sessions_state", "photo_upload_sessions", type_="check")
    op.create_check_constraint(
        "ck_photo_upload_sessions_state",
        "photo_upload_sessions",
        "state IN ('active', 'discarded', 'abandoned')",
    )
