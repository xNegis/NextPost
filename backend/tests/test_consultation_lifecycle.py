import pytest

from app import consultation_access, models
from app.consultation_lifecycle import (
    TERMINAL_LIFECYCLES,
    ConsultationLifecycle,
    TransitionDecision,
    decide_transition,
)


def test_canonical_lifecycle_values_match_accepted_contract() -> None:
    assert [member.value for member in ConsultationLifecycle] == [
        "open",
        "finalized",
        "deleted",
        "removed",
    ]
    assert TERMINAL_LIFECYCLES == {
        ConsultationLifecycle.finalized,
        ConsultationLifecycle.deleted,
        ConsultationLifecycle.removed,
    }


def test_persistence_and_access_reuse_the_same_lifecycle() -> None:
    # A code-only rename must not reintroduce a parallel, driftable enum.
    assert models.ConsultationState is ConsultationLifecycle
    assert consultation_access.ConsultationLifecycle is ConsultationLifecycle


@pytest.mark.parametrize(
    "target",
    [ConsultationLifecycle.finalized, ConsultationLifecycle.deleted, ConsultationLifecycle.removed],
)
def test_open_to_terminal_is_apply(target: ConsultationLifecycle) -> None:
    assert decide_transition(ConsultationLifecycle.open, target) == TransitionDecision.apply


@pytest.mark.parametrize(
    "state",
    [ConsultationLifecycle.finalized, ConsultationLifecycle.deleted, ConsultationLifecycle.removed],
)
def test_same_terminal_target_is_same_target(state: ConsultationLifecycle) -> None:
    assert decide_transition(state, state) == TransitionDecision.same_target


@pytest.mark.parametrize(
    "state",
    [ConsultationLifecycle.finalized, ConsultationLifecycle.deleted, ConsultationLifecycle.removed],
)
def test_terminal_to_open_is_conflict(state: ConsultationLifecycle) -> None:
    assert decide_transition(state, ConsultationLifecycle.open) == TransitionDecision.conflict


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ConsultationLifecycle.finalized, ConsultationLifecycle.deleted),
        (ConsultationLifecycle.finalized, ConsultationLifecycle.removed),
        (ConsultationLifecycle.deleted, ConsultationLifecycle.finalized),
        (ConsultationLifecycle.deleted, ConsultationLifecycle.removed),
        (ConsultationLifecycle.removed, ConsultationLifecycle.finalized),
        (ConsultationLifecycle.removed, ConsultationLifecycle.deleted),
    ],
)
def test_different_terminal_target_is_conflict(
    current: ConsultationLifecycle, target: ConsultationLifecycle
) -> None:
    assert decide_transition(current, target) == TransitionDecision.conflict


def test_open_to_open_is_conflict() -> None:
    assert decide_transition(ConsultationLifecycle.open, ConsultationLifecycle.open) == (
        TransitionDecision.conflict
    )


@pytest.mark.parametrize(
    "current",
    [None, "open", "finalized", 1, object()],
)
def test_unsupported_current_is_conflict(current: object) -> None:
    assert decide_transition(current, ConsultationLifecycle.deleted) == TransitionDecision.conflict


@pytest.mark.parametrize(
    "target",
    [None, "finalized", "deleted", "removed", 1, object()],
)
def test_unsupported_target_is_conflict(target: object) -> None:
    assert decide_transition(ConsultationLifecycle.open, target) == TransitionDecision.conflict


def test_policy_is_pure_and_importable_without_a_database() -> None:
    # The module performs no persistence, storage or authorization side effect. Importing it must
    # not require a database session, configuration or storage; the decision depends only on inputs.
    assert decide_transition(ConsultationLifecycle.open, ConsultationLifecycle.finalized) == (
        TransitionDecision.apply
    )
    # The inputs are not mutated.
    current = ConsultationLifecycle.open
    decide_transition(current, ConsultationLifecycle.deleted)
    assert current == ConsultationLifecycle.open


def test_transition_decision_never_authorizes_an_actor() -> None:
    # The policy returns only a classification; it has no account/owner concept and must not be
    # used as an authorization result.
    decision = decide_transition(ConsultationLifecycle.open, ConsultationLifecycle.deleted)
    assert decision is TransitionDecision.apply
    assert not hasattr(decision, "allowed")
