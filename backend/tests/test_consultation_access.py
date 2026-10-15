import uuid
from typing import cast

import pytest

from app.audience import PRIVATE, PUBLIC
from app.consultation_access import (
    AccessDecision,
    AccessOperation,
    AccessReason,
    AccessSnapshot,
    ConsultationLifecycle,
    can_access,
)
from app.private_link import PrivateLinkState, current_link_token, verify_current_link

SECRET = "nextpost-private-link-secret-test-only-0123456789"

OWNER_ID = str(uuid.uuid4())
OTHER_ID = str(uuid.uuid4())
CONSULTATION_ID = str(uuid.uuid4())


def _snapshot(
    *,
    audience: str = PUBLIC,
    lifecycle: ConsultationLifecycle = ConsultationLifecycle.open,
    active: bool = True,
    generation: int = 1,
) -> AccessSnapshot:
    return AccessSnapshot(
        consultation_id=CONSULTATION_ID,
        owner_id=OWNER_ID,
        audience=audience,
        lifecycle=lifecycle,
        private_link_active=active,
        private_link_generation=generation,
    )


def _verifier():
    def verify(state: PrivateLinkState, token: str | None) -> bool:
        return verify_current_link(state, token, SECRET)

    return verify


def _current_token(generation: int = 1) -> str:
    return current_link_token(PrivateLinkState(CONSULTATION_ID, generation, True), SECRET)


def test_anonymous_is_denied_for_every_operation() -> None:
    for operation in AccessOperation:
        decision = can_access(_snapshot(), None, None, operation, _verifier())
        assert decision == AccessDecision(False, AccessReason.unauthenticated)


@pytest.mark.parametrize(
    "lifecycle",
    [
        ConsultationLifecycle.finalized,
        ConsultationLifecycle.deleted,
        ConsultationLifecycle.removed,
    ],
)
def test_terminal_state_is_denied_even_for_owner(lifecycle: ConsultationLifecycle) -> None:
    for operation in AccessOperation:
        decision = can_access(
            _snapshot(lifecycle=lifecycle), OWNER_ID, None, operation, _verifier()
        )
        assert decision == AccessDecision(False, AccessReason.unavailable)


def test_owner_can_read_and_manage_without_token() -> None:
    for operation in (AccessOperation.read, AccessOperation.manage):
        decision = can_access(_snapshot(), OWNER_ID, None, operation, _verifier())
        assert decision == AccessDecision(True, AccessReason.allowed)


def test_owner_cannot_vote() -> None:
    decision = can_access(_snapshot(), OWNER_ID, None, AccessOperation.vote, _verifier())
    assert decision == AccessDecision(False, AccessReason.owner_cannot_vote)


def test_owner_reads_private_without_token() -> None:
    decision = can_access(
        _snapshot(audience=PRIVATE), OWNER_ID, None, AccessOperation.read, _verifier()
    )
    assert decision == AccessDecision(True, AccessReason.allowed)


def test_non_owner_cannot_manage() -> None:
    decision = can_access(_snapshot(), OTHER_ID, None, AccessOperation.manage, _verifier())
    assert decision == AccessDecision(False, AccessReason.unavailable)


def test_non_owner_reads_public_without_token() -> None:
    decision = can_access(
        _snapshot(audience=PUBLIC), OTHER_ID, None, AccessOperation.read, _verifier()
    )
    assert decision == AccessDecision(True, AccessReason.allowed)


def test_non_owner_votes_public_without_token() -> None:
    decision = can_access(
        _snapshot(audience=PUBLIC), OTHER_ID, None, AccessOperation.vote, _verifier()
    )
    assert decision == AccessDecision(True, AccessReason.allowed)


def test_non_owner_reads_private_only_with_current_token() -> None:
    snapshot = _snapshot(audience=PRIVATE)
    token = _current_token()

    assert can_access(
        snapshot, OTHER_ID, None, AccessOperation.read, _verifier()
    ) == AccessDecision(False, AccessReason.private_link_required)
    assert can_access(
        snapshot, OTHER_ID, token, AccessOperation.read, _verifier()
    ) == AccessDecision(True, AccessReason.allowed)


def test_private_link_is_never_inferred_from_ownership() -> None:
    snapshot = _snapshot(audience=PRIVATE)
    assert can_access(snapshot, OTHER_ID, None, AccessOperation.read, _verifier()).allowed is False


def test_stale_or_wrong_token_grants_no_access() -> None:
    snapshot = _snapshot(audience=PRIVATE)
    other_token = current_link_token(PrivateLinkState(str(uuid.uuid4()), 1, True), SECRET)
    assert can_access(snapshot, OTHER_ID, other_token, AccessOperation.read, _verifier()) == (
        AccessDecision(False, AccessReason.private_link_required)
    )


def test_disabled_private_link_denies_even_with_token() -> None:
    snapshot = _snapshot(audience=PRIVATE, active=False)
    token = _current_token()
    decision = can_access(snapshot, OTHER_ID, token, AccessOperation.read, _verifier())
    assert decision == AccessDecision(False, AccessReason.private_link_required)


def test_snapshot_generation_is_authoritative_for_verification() -> None:
    old_token = _current_token(generation=1)
    snapshot = _snapshot(audience=PRIVATE, generation=2)

    decision = can_access(snapshot, OTHER_ID, old_token, AccessOperation.read, _verifier())

    assert decision == AccessDecision(False, AccessReason.private_link_required)


def test_private_vote_requires_current_link() -> None:
    snapshot = _snapshot(audience=PRIVATE)
    token = _current_token()
    assert can_access(
        snapshot, OTHER_ID, token, AccessOperation.vote, _verifier()
    ) == AccessDecision(True, AccessReason.allowed)
    assert can_access(
        snapshot, OTHER_ID, None, AccessOperation.vote, _verifier()
    ) == AccessDecision(False, AccessReason.private_link_required)


def test_unknown_audience_is_denied() -> None:
    snapshot = _snapshot(audience="secret")
    decision = can_access(snapshot, OTHER_ID, None, AccessOperation.read, _verifier())
    assert decision == AccessDecision(False, AccessReason.unavailable)


def test_unknown_operation_is_denied() -> None:
    operation = cast(AccessOperation, "delete")
    decision = can_access(_snapshot(), OTHER_ID, None, operation, _verifier())
    assert decision == AccessDecision(False, AccessReason.unavailable)
