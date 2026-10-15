"""Private consultation link capability (RF-09).

A Private consultation has exactly one current shareable link. The link is a versioned HMAC-SHA-256
capability derived from the consultation UUID, a positive integer generation and a dedicated
server-only ``PRIVATE_LINK_SECRET``. The stored ``(consultation_id, generation, active)`` state lets
the owner re-copy the same link without storing a bearer token, while revoking or replacing the link
simply changes that state.

RF-10 persists this state alongside the Consultation in its own migration and calls these pure
functions from its routes. No database commit, endpoint or side effect happens here.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid
from dataclasses import dataclass

_TOKEN_PREFIX = "v1."
_DOMAIN = b"nextpost-private-link-v1"
_TOKEN_SUFFIX_LENGTH = 43
_GENERATION_MAX = (1 << 64) - 1
_SECRET_MIN_BYTES = 32
_B64URL_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")

_CONFLICT = "conflict"
_OK = "ok"
_OVERFLOW = "overflow"


@dataclass(frozen=True)
class PrivateLinkState:
    """Current private-link state for one consultation."""

    consultation_id: str
    generation: int
    active: bool


@dataclass(frozen=True)
class LinkTransition:
    """Result of a pure link lifecycle transition."""

    ok: bool
    state: PrivateLinkState | None
    reason: str


def _consultation_uuid(consultation_id: str) -> uuid.UUID:
    return uuid.UUID(consultation_id)


def _is_supported_generation(generation: object) -> bool:
    return (
        isinstance(generation, int)
        and not isinstance(generation, bool)
        and 1 <= generation <= _GENERATION_MAX
    )


def parse_generation(value: object) -> int | None:
    """Parse a supported positive generation from a decimal string or integer.

    Returns ``None`` for anything that is not a canonical, in-range generation. RF-10 persists and
    transports generations as decimal strings so JavaScript loses no precision over the full
    unsigned 64-bit domain.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if _is_supported_generation(value) else None
    if isinstance(value, str):
        text = value.strip()
        if not text or not text.isascii() or not text.isdigit():
            return None
        try:
            parsed = int(text)
        except ValueError:
            return None
        return parsed if _is_supported_generation(parsed) else None
    return None


def _generation_bytes(generation: int) -> bytes:
    if not _is_supported_generation(generation):
        raise ValueError("generation must be a positive integer")
    return generation.to_bytes(8, "big")


def _digest(consultation_id: str, generation: int, secret: str) -> bytes:
    if not isinstance(secret, str) or len(secret.encode("utf-8")) < _SECRET_MIN_BYTES:
        raise ValueError("secret must be at least 32 bytes")
    uid = _consultation_uuid(consultation_id)
    message = _DOMAIN + b"\x00" + uid.bytes + _generation_bytes(generation)
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()


def current_link_token(state: PrivateLinkState, secret: str) -> str:
    """Derive the deterministic URL-safe capability for the current state."""
    if not state.active:
        raise ValueError("cannot derive a link token for inactive state")
    suffix = base64.urlsafe_b64encode(_digest(state.consultation_id, state.generation, secret))
    return _TOKEN_PREFIX + suffix.decode("ascii").rstrip("=")


def _is_valid_token_syntax(token: str) -> bool:
    if not token.startswith(_TOKEN_PREFIX):
        return False
    suffix = token[len(_TOKEN_PREFIX) :]
    if len(suffix) != _TOKEN_SUFFIX_LENGTH:
        return False
    return all(char in _B64URL_ALPHABET for char in suffix)


def verify_current_link(state: PrivateLinkState, presented: str | None, secret: str) -> bool:
    """Return whether ``presented`` is the current active link, in constant time.

    A disabled (inactive) link never verifies, and a malformed token is rejected before comparison.
    """
    if not isinstance(presented, str):
        return False
    if not state.active:
        return False
    if not _is_valid_token_syntax(presented):
        return False
    return hmac.compare_digest(current_link_token(state, secret), presented)


def disable_link(state: PrivateLinkState, expected_generation: int) -> LinkTransition:
    """Disable the link without changing the generation (requires current generation)."""
    if not _is_supported_generation(state.generation) or not _is_supported_generation(
        expected_generation
    ):
        return LinkTransition(False, None, _CONFLICT)
    if expected_generation != state.generation:
        return LinkTransition(False, None, _CONFLICT)
    if not state.active:
        return LinkTransition(False, None, _CONFLICT)
    return LinkTransition(
        True, PrivateLinkState(state.consultation_id, state.generation, False), _OK
    )


def replace_link(state: PrivateLinkState, expected_generation: int) -> LinkTransition:
    """Rotate to a new link while active, invalidating the previous token."""
    if not _is_supported_generation(state.generation) or not _is_supported_generation(
        expected_generation
    ):
        return LinkTransition(False, None, _CONFLICT)
    if expected_generation != state.generation:
        return LinkTransition(False, None, _CONFLICT)
    if not state.active:
        return LinkTransition(False, None, _CONFLICT)
    if state.generation >= _GENERATION_MAX:
        return LinkTransition(False, None, _OVERFLOW)
    return LinkTransition(
        True, PrivateLinkState(state.consultation_id, state.generation + 1, True), _OK
    )


def create_new_link(state: PrivateLinkState, expected_generation: int) -> LinkTransition:
    """Create a fresh link while disabled, re-enabling access."""
    if not _is_supported_generation(state.generation) or not _is_supported_generation(
        expected_generation
    ):
        return LinkTransition(False, None, _CONFLICT)
    if expected_generation != state.generation:
        return LinkTransition(False, None, _CONFLICT)
    if state.active:
        return LinkTransition(False, None, _CONFLICT)
    if state.generation >= _GENERATION_MAX:
        return LinkTransition(False, None, _OVERFLOW)
    return LinkTransition(
        True, PrivateLinkState(state.consultation_id, state.generation + 1, True), _OK
    )
