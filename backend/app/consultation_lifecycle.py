"""Canonical consultation lifecycle and pure terminal-transition policy (RF-11).

A persisted consultation has exactly one of four internal lifecycle values: ``open``,
``finalized``, ``deleted`` or ``removed``. Publication creates only ``open``; the three terminal
values are produced only by their owning consumer operations (RF-13 author deletion, RF-19/RF-20
finalization, and the restricted RF-32 administrator-removal command). ``unavailable`` is an
external access result, not a persisted lifecycle, and temporary preparation belongs to
``PhotoUploadSessionState`` rather than to a ``Consultation`` row.

This module is the single source of truth for those values. Persistence and the access policy both
import ``ConsultationLifecycle`` from here so a future code-only rename cannot silently drift from
Alembic revision ``20260928_0004``, which fixes the exact ``open|finalized|deleted|removed``
strings. There is no automatic expiry, duration, reopening or lifecycle-transition date; the
existing ``published_at`` remains the only product event date.

Consumer transition protocol (FR-4, DEC-033):

1. Authenticate and authorize the actor for the requested operation.
2. Begin the transaction and lock the consultation row with PostgreSQL ``FOR UPDATE``.
3. Read the current lifecycle under that lock.
4. Evaluate ``decide_transition`` with the latest committed state and the intended terminal target.
5. For ``apply``, perform every required database side effect in the same transaction and write the
   terminal state as part of that same atomic unit.
6. Commit once. Only after durable database revocation may physical-file deletion/retry proceed
   according to RF-37; a file-deletion failure must not restore access.
7. For ``same_target``, return the existing result only after the operation and payload identity are
   proven; ``same_target`` alone is never proof of idempotency.
8. For ``conflict``, change nothing and return a safe, owner-appropriate conflict.

There is no priority ordering between finalization, author deletion and administrator removal: the
first terminal transaction that commits wins, and a losing operation must not overwrite, reinterpret
or reopen the result.

This module has no FastAPI, SQLAlchemy, storage or configuration dependency and performs no side
effect. It cannot authorize an actor; authorization remains the access policy's job.
"""

from __future__ import annotations

from enum import Enum


class ConsultationLifecycle(str, Enum):
    """The canonical persisted lifecycle of a consultation."""

    open = "open"
    finalized = "finalized"
    deleted = "deleted"
    removed = "removed"


TERMINAL_LIFECYCLES = frozenset(
    {
        ConsultationLifecycle.finalized,
        ConsultationLifecycle.deleted,
        ConsultationLifecycle.removed,
    }
)


class TransitionDecision(str, Enum):
    """Outcome of evaluating a requested terminal transition."""

    apply = "apply"
    same_target = "same_target"
    conflict = "conflict"


def decide_transition(current: object, target: object) -> TransitionDecision:
    """Classify a requested terminal transition without performing any side effect.

    ``current`` is the latest committed consultation lifecycle and ``target`` is the terminal state
    the consumer intends to write. The result is one of:

    - ``apply``: ``current`` is ``open`` and ``target`` is a valid terminal state;
    - ``same_target``: ``current`` already equals ``target`` (a retry candidate, never proof of
      idempotency by itself);
    - ``conflict``: either input is unsupported, the target is ``open`` (which would reopen a
      terminal consultation or describe a non-terminal transition), or the current state is terminal
      and differs from the requested target.

    A consumer that receives ``same_target`` must still prove the operation and payload are
    identical before returning the existing result (DEC-033); without matching evidence it must
    return a safe conflict.
    """
    if not isinstance(current, ConsultationLifecycle):
        return TransitionDecision.conflict
    if not isinstance(target, ConsultationLifecycle) or target == ConsultationLifecycle.open:
        return TransitionDecision.conflict
    if current == ConsultationLifecycle.open:
        return TransitionDecision.apply
    if current == target:
        return TransitionDecision.same_target
    return TransitionDecision.conflict
