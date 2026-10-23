"""Add the voter-first chronological index for participant history (RF-21).

Revision ID: 20261021_0009
Revises: 20261020_0008
Create Date: 2026-10-21

Additive index-only migration. The participant-history projection reads the current account's
immutable ``Vote`` rows scoped by ``voter_id`` and orders them by ``created_at`` with the
consultation id as a deterministic tie-breaker. This composite index serves that voter-first
chronological access without a full table scan. Outcome ordering reuses the existing
``ix_outcomes_voter`` index joined through the ``consultation_finalizations`` primary key, so no
redundant outcome index is introduced. Downgrade drops only the new index and leaves every vote and
outcome untouched.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261021_0009"
down_revision: str | None = "20261020_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_votes_voter_created",
        "votes",
        ["voter_id", "created_at", "consultation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_votes_voter_created", table_name="votes")
