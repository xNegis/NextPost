import uuid

import pytest

from app.private_link import (
    _GENERATION_MAX,
    PrivateLinkState,
    create_new_link,
    current_link_token,
    disable_link,
    replace_link,
    verify_current_link,
)

SECRET = "nextpost-private-link-secret-test-only-0123456789"
OTHER_SECRET = "another-private-link-secret-test-only-9876543210"


def _state(consultation_id: str, generation: int, active: bool = True) -> PrivateLinkState:
    return PrivateLinkState(consultation_id=consultation_id, generation=generation, active=active)


def test_token_is_stable_for_owner_recopy() -> None:
    state = _state(str(uuid.uuid4()), 1)
    assert current_link_token(state, SECRET) == current_link_token(state, SECRET)


def test_token_has_expected_shape() -> None:
    token = current_link_token(_state(str(uuid.uuid4()), 1), SECRET)
    assert token.startswith("v1.")
    assert len(token) == len("v1.") + 43


def test_different_consultations_yield_different_tokens() -> None:
    first = current_link_token(_state(str(uuid.uuid4()), 1), SECRET)
    second = current_link_token(_state(str(uuid.uuid4()), 1), SECRET)
    assert first != second


def test_different_generations_yield_different_tokens() -> None:
    consultation_id = str(uuid.uuid4())
    first = current_link_token(_state(consultation_id, 1), SECRET)
    second = current_link_token(_state(consultation_id, 2), SECRET)
    assert first != second


def test_different_secrets_yield_different_tokens() -> None:
    state = _state(str(uuid.uuid4()), 1)
    assert current_link_token(state, SECRET) != current_link_token(state, OTHER_SECRET)


def test_verify_accepts_current_token() -> None:
    state = _state(str(uuid.uuid4()), 1)
    assert verify_current_link(state, current_link_token(state, SECRET), SECRET) is True


def test_verify_rejects_wrong_consultation_token() -> None:
    state = _state(str(uuid.uuid4()), 1)
    other = current_link_token(_state(str(uuid.uuid4()), 1), SECRET)
    assert verify_current_link(state, other, SECRET) is False


def test_verify_rejects_old_generation_token() -> None:
    consultation_id = str(uuid.uuid4())
    old = current_link_token(_state(consultation_id, 1), SECRET)
    current = _state(consultation_id, 2)
    assert verify_current_link(current, old, SECRET) is False


def test_verify_rejects_disabled_link() -> None:
    consultation_id = str(uuid.uuid4())
    active_state = _state(consultation_id, 1)
    token = current_link_token(active_state, SECRET)
    disabled_state = _state(consultation_id, 1, active=False)
    assert verify_current_link(disabled_state, token, SECRET) is False


def test_derivation_rejects_disabled_link() -> None:
    state = _state(str(uuid.uuid4()), 1, active=False)
    with pytest.raises(ValueError, match="inactive"):
        current_link_token(state, SECRET)


def test_verify_rejects_wrong_secret() -> None:
    state = _state(str(uuid.uuid4()), 1)
    token = current_link_token(state, SECRET)
    assert verify_current_link(state, token, OTHER_SECRET) is False


@pytest.mark.parametrize(
    "presented",
    [
        None,
        "",
        "v1",
        "v1.",
        "v1.abc",
        "v1." + "a" * 42,
        "v1." + "a" * 44,
        "v2." + "a" * 43,
        "v1." + "=" * 43,
        "v1." + "a" * 42 + "=",
        "not-a-token",
    ],
)
def test_verify_rejects_malformed_tokens(presented: object) -> None:
    state = _state(str(uuid.uuid4()), 1)
    assert verify_current_link(state, presented, SECRET) is False


def test_disable_link_sets_active_false_without_rotating() -> None:
    state = _state(str(uuid.uuid4()), 3)
    transition = disable_link(state, 3)

    assert transition.ok is True
    assert transition.state is not None
    assert transition.state.active is False
    assert transition.state.generation == 3


def test_disable_link_rejects_stale_generation() -> None:
    state = _state(str(uuid.uuid4()), 3)
    assert disable_link(state, 2).ok is False
    assert disable_link(state, 4).ok is False


def test_disable_link_rejects_when_already_disabled() -> None:
    state = _state(str(uuid.uuid4()), 3, active=False)
    assert disable_link(state, 3).ok is False


def test_replace_link_rotates_generation_and_stays_active() -> None:
    state = _state(str(uuid.uuid4()), 3)
    transition = replace_link(state, 3)

    assert transition.ok is True
    assert transition.state is not None
    assert transition.state.active is True
    assert transition.state.generation == 4


def test_replace_link_old_token_no_longer_verifies() -> None:
    consultation_id = str(uuid.uuid4())
    state = _state(consultation_id, 1)
    old_token = current_link_token(state, SECRET)
    transition = replace_link(state, 1)

    assert transition.state is not None
    assert verify_current_link(transition.state, old_token, SECRET) is False
    assert (
        verify_current_link(transition.state, current_link_token(transition.state, SECRET), SECRET)
        is True
    )


def test_replace_link_rejects_when_disabled() -> None:
    state = _state(str(uuid.uuid4()), 3, active=False)
    assert replace_link(state, 3).ok is False


def test_create_new_link_requires_disabled_state() -> None:
    active = _state(str(uuid.uuid4()), 3, active=True)
    assert create_new_link(active, 3).ok is False

    disabled = _state(str(uuid.uuid4()), 3, active=False)
    transition = create_new_link(disabled, 3)
    assert transition.ok is True
    assert transition.state is not None
    assert transition.state.active is True
    assert transition.state.generation == 4


def test_create_new_link_rejects_stale_generation() -> None:
    state = _state(str(uuid.uuid4()), 3, active=False)
    assert create_new_link(state, 2).ok is False


def test_generation_overflow_fails_safely() -> None:
    state = _state(str(uuid.uuid4()), _GENERATION_MAX, active=True)
    assert replace_link(state, _GENERATION_MAX).ok is False

    disabled = _state(str(uuid.uuid4()), _GENERATION_MAX, active=False)
    assert create_new_link(disabled, _GENERATION_MAX).ok is False


@pytest.mark.parametrize("generation", [0, -1, True, _GENERATION_MAX + 1])
def test_transitions_reject_invalid_persisted_generation(generation: int) -> None:
    state = _state(str(uuid.uuid4()), generation)
    assert disable_link(state, generation).ok is False
    assert replace_link(state, generation).ok is False


@pytest.mark.parametrize("expected_generation", [0, -1, True, _GENERATION_MAX + 1])
def test_transitions_reject_invalid_expected_generation(expected_generation: int) -> None:
    active = _state(str(uuid.uuid4()), 1)
    disabled = _state(str(uuid.uuid4()), 1, active=False)
    assert disable_link(active, expected_generation).ok is False
    assert replace_link(active, expected_generation).ok is False
    assert create_new_link(disabled, expected_generation).ok is False


def test_derivation_rejects_invalid_generation() -> None:
    with pytest.raises(ValueError):
        current_link_token(_state(str(uuid.uuid4()), 0), SECRET)
    with pytest.raises(ValueError):
        current_link_token(_state(str(uuid.uuid4()), -1), SECRET)
    with pytest.raises(ValueError):
        current_link_token(_state(str(uuid.uuid4()), _GENERATION_MAX + 1), SECRET)


def test_derivation_rejects_malformed_consultation_id() -> None:
    with pytest.raises(ValueError):
        current_link_token(_state("not-a-uuid", 1), SECRET)


@pytest.mark.parametrize("secret", ["", "too-short"])
def test_derivation_rejects_weak_secret(secret: str) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        current_link_token(_state(str(uuid.uuid4()), 1), secret)
