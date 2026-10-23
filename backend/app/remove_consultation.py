"""Restricted non-interactive command for RF-32 consultation removal.

Run only from an approved backend deployment context. The command exposes no HTTP surface and uses
the server-side ``REMOVAL_OPERATOR_ID`` solely as an immutable audit label.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import uuid
from collections.abc import Callable, Mapping, Sequence
from typing import NoReturn

from sqlalchemy.orm import Session

from app.consultation_removal_service import (
    ALLOWED_REMOVAL_REASONS,
    RemovalInvalidError,
    RemovalResult,
    remove_consultation,
)
from app.consultation_service import ConsultationConflictError, ConsultationUnavailableError
from app.db import get_session_factory
from app.models import REMOVAL_OPERATOR_ID_MAX_LENGTH

logger = logging.getLogger(__name__)

EXIT_SUCCESS = 0
EXIT_INVALID = 2
EXIT_UNAVAILABLE = 3
EXIT_CONFLICT = 4
EXIT_INTERNAL = 5

_OPERATOR_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]*$")


class CommandInputError(Exception):
    """The non-interactive command input is invalid."""


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CommandInputError(message)


def _parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(description="Irreversibly remove one open consultation")
    parser.add_argument("--consultation-id", required=True)
    parser.add_argument("--confirm-consultation-id", required=True)
    parser.add_argument("--expected-state", required=True)
    parser.add_argument("--operation-id", required=True)
    parser.add_argument("--reason", required=True)
    return parser


def _canonical_uuid(raw: str, field: str) -> uuid.UUID:
    try:
        value = uuid.UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise CommandInputError(f"{field} must be a canonical UUID") from exc
    if str(value) != raw:
        raise CommandInputError(f"{field} must be a lowercase canonical UUID")
    return value


def _operator_id(environ: Mapping[str, str]) -> str:
    raw = environ.get("REMOVAL_OPERATOR_ID", "")
    value = raw.strip()
    if not value:
        raise CommandInputError("REMOVAL_OPERATOR_ID must be configured")
    if len(value) > REMOVAL_OPERATOR_ID_MAX_LENGTH or _OPERATOR_PATTERN.fullmatch(value) is None:
        raise CommandInputError("REMOVAL_OPERATOR_ID has an invalid format")
    return value


def _payload(result: RemovalResult) -> dict[str, object]:
    return {
        "classification": result.classification,
        "consultation_id": str(result.consultation_id),
        "images_marked": result.images_marked,
        "operation_id": str(result.operation_id),
        "previous_state": result.previous_state,
        "reason_code": result.reason_code,
        "removed_at": result.removed_at.isoformat(),
        "votes_removed": result.votes_removed,
    }


def _emit(payload: Mapping[str, object], *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    print(json.dumps(dict(payload), sort_keys=True, separators=(",", ":")), file=stream)


def run(
    argv: Sequence[str],
    *,
    environ: Mapping[str, str] | None = None,
    session_factory: Callable[[], Session] | None = None,
) -> int:
    """Execute the command contract and return its stable process exit code."""
    try:
        args = _parser().parse_args(list(argv))
        consultation_id = _canonical_uuid(args.consultation_id, "consultation_id")
        confirmation_id = _canonical_uuid(args.confirm_consultation_id, "confirm_consultation_id")
        if confirmation_id != consultation_id:
            raise CommandInputError("consultation confirmation does not match")
        if args.expected_state != "open":
            raise CommandInputError("expected_state must be open")
        operation_id = _canonical_uuid(args.operation_id, "operation_id")
        if args.reason not in ALLOWED_REMOVAL_REASONS:
            raise CommandInputError("reason is not supported")
        operator_id = _operator_id(environ if environ is not None else os.environ)
    except (CommandInputError, RemovalInvalidError):
        _emit({"classification": "invalid_input"}, error=True)
        return EXIT_INVALID

    factory = session_factory if session_factory is not None else get_session_factory()
    with factory() as db:
        try:
            result = remove_consultation(
                db,
                consultation_id=consultation_id,
                operation_id=operation_id,
                expected_state="open",
                operator_id=operator_id,
                reason_code=args.reason,
            )
        except ConsultationUnavailableError:
            db.rollback()
            _emit(
                {
                    "classification": "unavailable",
                    "consultation_id": str(consultation_id),
                    "operation_id": str(operation_id),
                },
                error=True,
            )
            return EXIT_UNAVAILABLE
        except ConsultationConflictError:
            db.rollback()
            _emit(
                {
                    "classification": "conflict",
                    "consultation_id": str(consultation_id),
                    "operation_id": str(operation_id),
                },
                error=True,
            )
            return EXIT_CONFLICT
        except RemovalInvalidError:
            db.rollback()
            _emit({"classification": "invalid_input"}, error=True)
            return EXIT_INVALID
        except Exception:
            db.rollback()
            logger.error(
                "restricted removal command failed: consultation_id=%s operation_id=%s",
                consultation_id,
                operation_id,
            )
            _emit(
                {
                    "classification": "internal_error",
                    "consultation_id": str(consultation_id),
                    "operation_id": str(operation_id),
                },
                error=True,
            )
            return EXIT_INTERNAL

    _emit(_payload(result))
    return EXIT_SUCCESS


def main() -> int:
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
