"""Make published media and terminal content detachable for verified erasure (RF-37).

Revision ID: 20261019_0006
Revises: 20261016_0005
Create Date: 2026-10-19

This migration is additive for current open data. It makes the option-to-image and
consultation-to-source-session relationships detachable, adds a non-visual media deletion
completion marker, and makes terminal-sanitized content fields safely nullable while adding
constraints that still require the complete publication contract for ``open`` consultations.

File bytes remain external to Alembic: upgrade and downgrade never unlink, restore or move them.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261019_0006"
down_revision: str | None = "20261016_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rebuild the two audience checks that would otherwise reject a NULL audience on a
    # terminal (sanitized) consultation.
    op.drop_constraint("ck_consultations_audience", "consultations", type_="check")
    op.drop_constraint("ck_consultations_audience_link", "consultations", type_="check")

    # Detachable source-session, publication fingerprint, question and audience.
    op.alter_column("consultations", "source_session_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column(
        "consultations", "fingerprint", existing_type=sa.String(length=64), nullable=True
    )
    op.alter_column("consultations", "question", existing_type=sa.Text(), nullable=True)
    op.alter_column("consultations", "audience", existing_type=sa.String(length=8), nullable=True)

    # Detachable option image with a non-visual verified-absence completion marker.
    op.alter_column("consultation_photos", "image_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column(
        "consultation_photos",
        sa.Column("media_deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_check_constraint(
        "ck_consultations_audience",
        "consultations",
        "audience IS NULL OR audience IN ('public', 'private')",
    )
    op.create_check_constraint(
        "ck_consultations_audience_link",
        "consultations",
        "(audience IS NULL) OR "
        "(audience = 'public' AND private_link_active = false) OR "
        "(audience = 'private' AND private_link_generation >= 1)",
    )
    op.create_check_constraint(
        "ck_consultations_open_complete",
        "consultations",
        "(state <> 'open') OR (question IS NOT NULL AND audience IS NOT NULL "
        "AND source_session_id IS NOT NULL AND fingerprint IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_consultation_photos_media",
        "consultation_photos",
        "(image_id IS NOT NULL AND media_deleted_at IS NULL) OR "
        "(image_id IS NULL AND media_deleted_at IS NOT NULL)",
    )

    # Cross-table invariant that the per-table checks cannot express: an ``open`` consultation
    # must retain every image association, so a photo may only be detached (image_id NULL) once its
    # consultation is terminal. Enforced with narrowly scoped deferred constraint triggers.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_open_consultation_media() RETURNS trigger AS $$
        BEGIN
            IF TG_TABLE_NAME = 'consultation_photos' THEN
                IF NEW.image_id IS NULL THEN
                    IF EXISTS (
                        SELECT 1 FROM consultations WHERE id = NEW.consultation_id AND state = 'open'
                    ) THEN
                        RAISE EXCEPTION 'cannot detach a photo from an open consultation'
                            USING ERRCODE = '23514';
                    END IF;
                END IF;
                RETURN NEW;
            ELSIF TG_TABLE_NAME = 'consultations' THEN
                IF NEW.state = 'open' THEN
                    IF EXISTS (
                        SELECT 1 FROM consultation_photos
                        WHERE consultation_id = NEW.id AND image_id IS NULL
                    ) THEN
                        RAISE EXCEPTION 'an open consultation cannot retain detached photos'
                            USING ERRCODE = '23514';
                    END IF;
                END IF;
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_consultation_photos_open_media "
        "AFTER INSERT OR UPDATE ON consultation_photos "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION check_open_consultation_media()"
    )
    op.execute(
        "CREATE CONSTRAINT TRIGGER trg_consultations_open_media "
        "AFTER INSERT OR UPDATE ON consultations "
        "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
        "EXECUTE FUNCTION check_open_consultation_media()"
    )


def downgrade() -> None:
    bind = op.get_bind()
    detached_options = bind.execute(
        sa.text(
            "SELECT count(*) FROM consultation_photos "
            "WHERE image_id IS NULL OR media_deleted_at IS NOT NULL"
        )
    ).scalar_one()
    sanitized_consultations = bind.execute(
        sa.text(
            "SELECT count(*) FROM consultations WHERE source_session_id IS NULL "
            "OR fingerprint IS NULL OR question IS NULL OR audience IS NULL"
        )
    ).scalar_one()
    if detached_options or sanitized_consultations:
        raise RuntimeError(
            "RF-37 downgrade refused: irreversible media detachment or terminal "
            "sanitization has already occurred"
        )

    op.execute("DROP TRIGGER IF EXISTS trg_consultation_photos_open_media ON consultation_photos")
    op.execute("DROP TRIGGER IF EXISTS trg_consultations_open_media ON consultations")
    op.execute("DROP FUNCTION IF EXISTS check_open_consultation_media()")

    op.drop_constraint("ck_consultation_photos_media", "consultation_photos", type_="check")
    op.drop_constraint("ck_consultations_open_complete", "consultations", type_="check")
    op.drop_constraint("ck_consultations_audience_link", "consultations", type_="check")
    op.drop_constraint("ck_consultations_audience", "consultations", type_="check")

    op.drop_column("consultation_photos", "media_deleted_at")
    op.alter_column("consultation_photos", "image_id", existing_type=sa.Uuid(), nullable=False)

    op.alter_column("consultations", "audience", existing_type=sa.String(length=8), nullable=False)
    op.alter_column("consultations", "question", existing_type=sa.Text(), nullable=False)
    op.alter_column(
        "consultations", "fingerprint", existing_type=sa.String(length=64), nullable=False
    )
    op.alter_column("consultations", "source_session_id", existing_type=sa.Uuid(), nullable=False)

    op.create_check_constraint(
        "ck_consultations_audience",
        "consultations",
        "audience IN ('public', 'private')",
    )
    op.create_check_constraint(
        "ck_consultations_audience_link",
        "consultations",
        "(audience = 'public' AND private_link_active = false) OR "
        "(audience = 'private' AND private_link_generation >= 1)",
    )
