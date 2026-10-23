import json
import uuid

import pytest

from app.remove_consultation import (
    EXIT_CONFLICT,
    EXIT_INTERNAL,
    EXIT_INVALID,
    EXIT_SUCCESS,
    EXIT_UNAVAILABLE,
    run,
)


def _argv(consultation_id: uuid.UUID, operation_id: uuid.UUID) -> list[str]:
    target = str(consultation_id)
    return [
        "--consultation-id",
        target,
        "--confirm-consultation-id",
        target,
        "--expected-state",
        "open",
        "--operation-id",
        str(operation_id),
        "--reason",
        "other",
    ]


@pytest.mark.parametrize(
    "argv,environ",
    [
        ([], {"REMOVAL_OPERATOR_ID": "ops.alice"}),
        (["--consultation-id", "not-a-uuid"], {"REMOVAL_OPERATOR_ID": "ops.alice"}),
        (
            _argv(uuid.uuid4(), uuid.uuid4())[:-1] + ["free text"],
            {"REMOVAL_OPERATOR_ID": "ops.alice"},
        ),
        (_argv(uuid.uuid4(), uuid.uuid4()), {}),
        (_argv(uuid.uuid4(), uuid.uuid4()), {"REMOVAL_OPERATOR_ID": "bad operator"}),
    ],
)
def test_invalid_inputs_return_sanitized_exit_two(argv, environ, capsys) -> None:
    assert run(argv, environ=environ, session_factory=lambda: None) == EXIT_INVALID
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {"classification": "invalid_input"}


def test_confirmation_must_repeat_target(capsys) -> None:
    consultation_id = uuid.uuid4()
    argv = _argv(consultation_id, uuid.uuid4())
    argv[3] = str(uuid.uuid4())
    assert run(argv, environ={"REMOVAL_OPERATOR_ID": "ops.alice"}) == EXIT_INVALID
    assert json.loads(capsys.readouterr().err)["classification"] == "invalid_input"


def test_uppercase_uuid_is_not_canonical(capsys) -> None:
    consultation_id = uuid.uuid4()
    argv = _argv(consultation_id, uuid.uuid4())
    argv[1] = str(consultation_id).upper()
    argv[3] = str(consultation_id).upper()
    assert run(argv, environ={"REMOVAL_OPERATOR_ID": "ops.alice"}) == EXIT_INVALID
    assert json.loads(capsys.readouterr().err)["classification"] == "invalid_input"


class _ContextSession:
    def __init__(self) -> None:
        self.rollback_called = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def rollback(self) -> None:
        self.rollback_called = True


@pytest.mark.parametrize(
    "error,expected_exit,classification",
    [
        ("unavailable", EXIT_UNAVAILABLE, "unavailable"),
        ("conflict", EXIT_CONFLICT, "conflict"),
        ("internal", EXIT_INTERNAL, "internal_error"),
    ],
)
def test_domain_failures_have_stable_sanitized_exits(
    monkeypatch, capsys, error, expected_exit, classification
) -> None:
    from app import remove_consultation as command
    from app.consultation_service import ConsultationConflictError, ConsultationUnavailableError

    def fail(*_args, **_kwargs):
        if error == "unavailable":
            raise ConsultationUnavailableError()
        if error == "conflict":
            raise ConsultationConflictError()
        raise RuntimeError("secret database payload")

    monkeypatch.setattr(command, "remove_consultation", fail)
    db = _ContextSession()
    result = run(
        _argv(uuid.uuid4(), uuid.uuid4()),
        environ={"REMOVAL_OPERATOR_ID": "ops.alice"},
        session_factory=lambda: db,
    )
    assert result == expected_exit
    payload = json.loads(capsys.readouterr().err)
    assert payload["classification"] == classification
    assert "secret" not in json.dumps(payload)
    assert db.rollback_called is True


def test_success_output_is_structured_and_omits_operator(monkeypatch, capsys) -> None:
    from datetime import datetime, timezone

    from app import remove_consultation as command
    from app.consultation_removal_service import RemovalResult

    consultation_id = uuid.uuid4()
    operation_id = uuid.uuid4()

    def succeed(*_args, **_kwargs):
        return RemovalResult(
            consultation_id=consultation_id,
            operation_id=operation_id,
            previous_state="open",
            reason_code="other",
            removed_at=datetime(2026, 10, 23, tzinfo=timezone.utc),
            classification="first",
            votes_removed=2,
            images_marked=2,
        )

    monkeypatch.setattr(command, "remove_consultation", succeed)
    result = run(
        _argv(consultation_id, operation_id),
        environ={"REMOVAL_OPERATOR_ID": "ops.alice"},
        session_factory=_ContextSession,
    )
    assert result == EXIT_SUCCESS
    payload = json.loads(capsys.readouterr().out)
    assert payload["classification"] == "first"
    assert payload["consultation_id"] == str(consultation_id)
    assert "operator" not in payload


def test_restricted_removal_has_no_http_or_openapi_surface() -> None:
    from app.main import app

    paths = app.openapi()["paths"]
    assert all("remove" not in path and "/admin" not in path for path in paths)
