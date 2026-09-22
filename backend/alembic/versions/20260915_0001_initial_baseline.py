"""Establish the initial NextPost migration baseline.

Revision ID: 20260915_0001
Revises:
Create Date: 2026-09-15
"""

from collections.abc import Sequence

revision: str = "20260915_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reserve the first migration revision without inventing product tables."""


def downgrade() -> None:
    """Return to the pre-schema baseline."""
