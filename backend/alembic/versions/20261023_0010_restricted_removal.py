"""Add immutable restricted consultation-removal records (RF-32).

Revision ID: 20261023_0010
Revises: 20261021_0009
Create Date: 2026-10-23

The migration is additive and deliberately does not fabricate provenance for historical
``removed`` consultations. Downgrade is allowed only before the operation has been used, because
dropping a populated table would destroy both the administrative audit and exact-replay identity.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261023_0010"
down_revision: str | None = "20261021_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consultation_removals",
        sa.Column("consultation_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operator_id", sa.String(length=128), nullable=False),
        sa.Column("reason_code", sa.String(length=32), nullable=False),
        sa.Column("previous_state", sa.String(length=16), nullable=False),
        sa.CheckConstraint(
            "length(operator_id) BETWEEN 1 AND 128",
            name="ck_consultation_removals_operator_id",
        ),
        sa.CheckConstraint(
            "reason_code IN ('rights_or_privacy', 'safety_or_abuse', "
            "'vote_integrity', 'other')",
            name="ck_consultation_removals_reason_code",
        ),
        sa.CheckConstraint(
            "previous_state = 'open'",
            name="ck_consultation_removals_previous_state",
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            name="fk_consultation_removals_consultation_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("consultation_id"),
        sa.UniqueConstraint("operation_id", name="uq_consultation_removals_operation_id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    count = bind.execute(sa.text("SELECT count(*) FROM consultation_removals")).scalar_one()
    if count:
        raise RuntimeError(
            "RF-32 downgrade refused: restricted consultation-removal records already exist"
        )
    op.drop_table("consultation_removals")
