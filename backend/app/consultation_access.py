"""Authoritative consultation access policy (RF-09).

A single pure decision function answers whether a current account may perform an operation on a
consultation, given a typed snapshot of the consultation's current state and the presented private
link token. RF-10, RF-14 and RF-16 must call it with the current database state on every protected
detail, text, image and vote request; no client-side check counts as authorization.

Consumer contract for RF-10 (and later readers):

- Assemble an ``AccessSnapshot`` from the persisted consultation row and its private-link state.
  Bind ``verify_token`` to ``verify_current_link`` using that row's link state and the configured
  ``PRIVATE_LINK_SECRET``.
- Call ``can_access`` for every protected read and vote. The decision reason is internal only;
  collapse denied reads to the generic unavailable response (DEC-028) and a missing session to the
  established 401 ``unauthenticated`` state.
- Link mutations are authorized separately via ``can_access(..., operation=manage)`` and then
  applied with the current generation under a row lock or compare-and-swap (see ``private_link``).
- Owner outcome/history views are a separate data contract and are not covered by this policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from app.audience import PRIVATE, PUBLIC, Audience
from app.consultation_lifecycle import ConsultationLifecycle
from app.private_link import PrivateLinkState


class AccessOperation(str, Enum):
    read = "read"
    vote = "vote"
    manage = "manage"


class AccessReason(str, Enum):
    allowed = "allowed"
    unauthenticated = "unauthenticated"
    unavailable = "unavailable"
    private_link_required = "private_link_required"
    owner_cannot_vote = "owner_cannot_vote"


@dataclass(frozen=True)
class AccessSnapshot:
    consultation_id: str
    owner_id: str
    audience: Audience
    lifecycle: ConsultationLifecycle
    private_link_active: bool
    private_link_generation: int


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: AccessReason


TokenVerifier = Callable[[PrivateLinkState, str | None], bool]


def can_access(
    snapshot: AccessSnapshot,
    account_id: str | None,
    presented_token: str | None,
    operation: AccessOperation,
    verify_token: TokenVerifier,
) -> AccessDecision:
    """Decide access using the current snapshot, account, presented token and operation.

    ``verify_token`` encapsulates the configured secret while this function constructs the link
    state from the same current snapshot used for the rest of the authorization decision. This
    prevents a caller from accidentally verifying against a different consultation generation.
    """
    if account_id is None:
        return AccessDecision(False, AccessReason.unauthenticated)

    if snapshot.lifecycle != ConsultationLifecycle.open:
        return AccessDecision(False, AccessReason.unavailable)

    if not isinstance(operation, AccessOperation):
        return AccessDecision(False, AccessReason.unavailable)

    is_owner = account_id == snapshot.owner_id

    if operation == AccessOperation.manage:
        if is_owner:
            return AccessDecision(True, AccessReason.allowed)
        return AccessDecision(False, AccessReason.unavailable)

    if is_owner:
        if operation == AccessOperation.vote:
            return AccessDecision(False, AccessReason.owner_cannot_vote)
        return AccessDecision(True, AccessReason.allowed)

    if snapshot.audience == PUBLIC:
        return AccessDecision(True, AccessReason.allowed)

    if snapshot.audience == PRIVATE:
        link_state = PrivateLinkState(
            consultation_id=snapshot.consultation_id,
            generation=snapshot.private_link_generation,
            active=snapshot.private_link_active,
        )
        if verify_token(link_state, presented_token):
            return AccessDecision(True, AccessReason.allowed)
        return AccessDecision(False, AccessReason.private_link_required)

    return AccessDecision(False, AccessReason.unavailable)
