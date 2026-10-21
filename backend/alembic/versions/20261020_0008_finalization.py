"""Add the finalization, declaration, snapshot and outcome records (RF-19/RF-20).

Revision ID: 20261020_0008
Revises: 20261020_0007
Create Date: 2026-10-20

Additive migration: open and voted data are preserved and no historical backfill is invented.
New tables hold the immutable finalization header (operation identity + canonical payload
fingerprint + denominator), the declared selections, one definitive count per stable option and
one private account-linked outcome per valid voter. Selections and counts use a composite foreign
key back to the stable option so every referenced option is proven to belong to the consultation.
Downgrade refuses once any finalization, selection, count or outcome has been persisted because the
winning transaction has already deleted the raw votes and images it replaced.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261020_0008"
down_revision: str | None = "20261020_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consultation_finalizations",
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("payload_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_votes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            name="fk_finalizations_consultation_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("consultation_id"),
        sa.UniqueConstraint("operation_id", name="uq_finalizations_operation_id"),
        sa.CheckConstraint("total_votes >= 0", name="ck_finalizations_total_votes"),
    )

    op.create_table(
        "consultation_final_selections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("consultation_photo_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["consultation_id", "consultation_photo_id"],
            ["consultation_photos.consultation_id", "consultation_photos.id"],
            name="fk_final_selections_photo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultation_finalizations.consultation_id"],
            name="fk_final_selections_finalization",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            "consultation_photo_id",
            name="uq_final_selections_consultation_photo",
        ),
    )
    op.create_index(
        "ix_final_selections_consultation",
        "consultation_final_selections",
        ["consultation_id"],
    )

    op.create_table(
        "consultation_final_option_counts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("consultation_photo_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("vote_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["consultation_id", "consultation_photo_id"],
            ["consultation_photos.consultation_id", "consultation_photos.id"],
            name="fk_final_option_counts_photo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultation_finalizations.consultation_id"],
            name="fk_final_option_counts_finalization",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            "consultation_photo_id",
            name="uq_final_option_counts_consultation_photo",
        ),
        sa.CheckConstraint("vote_count >= 0", name="ck_final_option_counts_vote_count"),
    )
    op.create_index(
        "ix_final_option_counts_consultation",
        "consultation_final_option_counts",
        ["consultation_id"],
    )

    op.create_table(
        "consultation_outcomes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("voter_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            name="fk_outcomes_consultation_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["voter_id"],
            ["accounts.id"],
            name="fk_outcomes_voter_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            "voter_id",
            name="uq_outcomes_consultation_voter",
        ),
        sa.CheckConstraint(
            "outcome IN ('matched', 'not_matched', 'no_choice')",
            name="ck_outcomes_outcome",
        ),
    )
    op.create_index("ix_outcomes_consultation", "consultation_outcomes", ["consultation_id"])
    op.create_index("ix_outcomes_voter", "consultation_outcomes", ["voter_id"])


def downgrade() -> None:
    bind = op.get_bind()
    for table in (
        "consultation_finalizations",
        "consultation_final_selections",
        "consultation_final_option_counts",
        "consultation_outcomes",
    ):
        count = bind.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
        if count:
            raise RuntimeError(
                "RF-19/RF-20 downgrade refused: finalization, selection, count or outcome "
                "records already exist"
            )

    op.drop_index("ix_outcomes_voter", table_name="consultation_outcomes")
    op.drop_index("ix_outcomes_consultation", table_name="consultation_outcomes")
    op.drop_table("consultation_outcomes")

    op.drop_index(
        "ix_final_option_counts_consultation", table_name="consultation_final_option_counts"
    )
    op.drop_table("consultation_final_option_counts")

    op.drop_index("ix_final_selections_consultation", table_name="consultation_final_selections")
    op.drop_table("consultation_final_selections")

    op.drop_table("consultation_finalizations")
