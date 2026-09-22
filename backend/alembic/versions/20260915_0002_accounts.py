"""Create the accounts table.

Revision ID: 20260915_0002
Revises: 20260915_0001
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260915_0002"
down_revision: str | None = "20260915_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("alias", sa.String(length=30), nullable=False),
        sa.Column("alias_canonical", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_accounts_email"),
        sa.UniqueConstraint("alias_canonical", name="uq_accounts_alias_canonical"),
    )


def downgrade() -> None:
    op.drop_table("accounts")
