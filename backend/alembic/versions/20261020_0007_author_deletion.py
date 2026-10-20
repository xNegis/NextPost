"""Add the irreversible voluntary author-deletion marker (RF-13).

Revision ID: 20261020_0007
Revises: 20261019_0006
Create Date: 2026-10-20

This migration is additive: existing open and finalized rows remain visible with a NULL marker,
and existing ``deleted``/``removed`` rows remain excluded through lifecycle. It adds a nullable
``author_deleted_at`` timestamp, a check that a non-null marker only coexists with the ``deleted``
or ``finalized`` lifecycle, and an owner/state/marker index so both My consultations tabs filter
before stable pagination. Downgrade refuses once any irreversible marker is populated.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261020_0007"
down_revision: str | None = "20261019_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "consultations",
        sa.Column("author_deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_consultations_author_deleted",
        "consultations",
        "author_deleted_at IS NULL OR state IN ('deleted', 'finalized')",
    )
    op.create_index(
        "ix_consultations_owner_state_author_deleted",
        "consultations",
        ["owner_id", "state", "author_deleted_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    marked = bind.execute(
        sa.text("SELECT count(*) FROM consultations WHERE author_deleted_at IS NOT NULL")
    ).scalar_one()
    if marked:
        raise RuntimeError(
            "RF-13 downgrade refused: irreversible author deletion markers already exist"
        )

    op.drop_index("ix_consultations_owner_state_author_deleted", table_name="consultations")
    op.drop_constraint("ck_consultations_author_deleted", "consultations", type_="check")
    op.drop_column("consultations", "author_deleted_at")
