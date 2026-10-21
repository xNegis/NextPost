"""Photo-free finalized-result read model (RF-19/RF-20).

This module owns the durable, normalized finalization projections that the author-only finalized
list/detail and the finalize API return. It is deliberately separated from the finalization write
service so ``consultation_service`` (owner projections) can consume it without creating a module
import cycle. It reads only the replacement records written by the winning finalization
transaction; a consultation without a finalization header (a legacy finalized row) yields ``None``
so consumers can render an honest ``Final result unavailable`` summary.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ConsultationFinalization,
    ConsultationFinalOptionCount,
    ConsultationFinalSelection,
)
from app.photo_service import _as_naive_utc


@dataclass(frozen=True)
class FinalizedOption:
    ordinal: int
    vote_count: int
    selected: bool


@dataclass(frozen=True)
class FinalizedResultSummary:
    finalized_at: datetime
    total_votes: int
    declaration: Literal["selected", "none"]
    selected_ordinals: list[int]
    options: list[FinalizedOption]


def build_finalized_summary(
    db: Session, consultation_id: uuid.UUID
) -> FinalizedResultSummary | None:
    """Return the definitive photo-free summary for one finalized consultation, or ``None``."""
    summaries = build_finalized_summaries(db, [consultation_id])
    return summaries.get(consultation_id)


def build_finalized_summaries(
    db: Session, consultation_ids: list[uuid.UUID]
) -> dict[uuid.UUID, FinalizedResultSummary | None]:
    """Return the definitive photo-free summary for each finalized consultation in one set of reads.

    The result for a consultation is ``None`` when no finalization header exists, which is exactly
    the legacy-finalized case: the consultation is terminal but predates the outcome contract, so no
    declaration, counts or outcome may be fabricated.
    """
    if not consultation_ids:
        return {}

    headers = db.scalars(
        select(ConsultationFinalization).where(
            ConsultationFinalization.consultation_id.in_(consultation_ids)
        )
    ).all()

    selections_by_consultation: dict[uuid.UUID, list[ConsultationFinalSelection]] = {}
    for selection in db.scalars(
        select(ConsultationFinalSelection)
        .where(ConsultationFinalSelection.consultation_id.in_(consultation_ids))
        .order_by(ConsultationFinalSelection.ordinal)
    ).all():
        selections_by_consultation.setdefault(selection.consultation_id, []).append(selection)

    counts_by_consultation: dict[uuid.UUID, list[ConsultationFinalOptionCount]] = {}
    for row in db.scalars(
        select(ConsultationFinalOptionCount)
        .where(ConsultationFinalOptionCount.consultation_id.in_(consultation_ids))
        .order_by(ConsultationFinalOptionCount.ordinal)
    ).all():
        counts_by_consultation.setdefault(row.consultation_id, []).append(row)

    summaries: dict[uuid.UUID, FinalizedResultSummary | None] = {
        consultation_id: None for consultation_id in consultation_ids
    }
    for header in headers:
        selections = selections_by_consultation.get(header.consultation_id, [])
        selected_ids = {selection.consultation_photo_id for selection in selections}
        count_rows = counts_by_consultation.get(header.consultation_id, [])
        options = [
            FinalizedOption(
                ordinal=int(row.ordinal),
                vote_count=int(row.vote_count),
                selected=row.consultation_photo_id in selected_ids,
            )
            for row in count_rows
        ]
        summaries[header.consultation_id] = FinalizedResultSummary(
            finalized_at=_as_naive_utc(header.finalized_at),
            total_votes=int(header.total_votes),
            declaration="none" if not selections else "selected",
            selected_ordinals=[selection.ordinal for selection in selections],
            options=options,
        )
    return summaries
