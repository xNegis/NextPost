"""Add immutable votes with same-consultation option integrity.

Revision ID: 20261016_0005
Revises: 20260928_0004
Create Date: 2026-10-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261016_0005"
down_revision: str | None = "20260928_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Candidate key referenced by the composite vote foreign key below, proving a vote's
    # selected option belongs to the same consultation it references.
    op.create_unique_constraint(
        "uq_consultation_photos_consultation_id",
        "consultation_photos",
        ["consultation_id", "id"],
    )

    op.create_table(
        "votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("voter_id", sa.Uuid(), nullable=False),
        sa.Column("consultation_photo_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            name="fk_votes_consultation_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["voter_id"],
            ["accounts.id"],
            name="fk_votes_voter_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id", "consultation_photo_id"],
            ["consultation_photos.consultation_id", "consultation_photos.id"],
            name="fk_votes_consultation_photo",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consultation_id", "voter_id", name="uq_votes_consultation_voter"),
    )
    op.create_index(
        "ix_votes_consultation_photo",
        "votes",
        ["consultation_id", "consultation_photo_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    vote_count = bind.execute(sa.text("SELECT count(*) FROM votes")).scalar_one()
    if vote_count:
        raise RuntimeError("RF-16 downgrade refused: votes exist")

    op.drop_index("ix_votes_consultation_photo", table_name="votes")
    op.drop_table("votes")
    op.drop_constraint(
        "uq_consultation_photos_consultation_id",
        "consultation_photos",
        type_="unique",
    )
