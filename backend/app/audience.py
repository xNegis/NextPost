"""Canonical consultation audience values and strict validation (RF-09).

The audience is fixed at publication (DEC-018/022/024). ``public`` is discoverable and viewable by
any registered account; ``private`` is unlisted and viewable only by a registered account that
holds the current private link. Neither audience permits anonymous photo viewing.

RF-06 consumes ``validate_audience`` for its controlled selector and RF-10 reuses it in the atomic
publication request. The frontend keeps an equivalent rule in ``frontend/src/audience.ts``; the two
must reject the same inputs.
"""

from typing import Literal

Audience = Literal["public", "private"]

PUBLIC: Audience = "public"
PRIVATE: Audience = "private"

AUDIENCE_MISSING_MESSAGE = "Choose an audience."
AUDIENCE_INVALID_MESSAGE = "Choose Public or Private."


def validate_audience(value: object) -> tuple[Audience | None, str | None]:
    """Return ``(normalized audience, error)``.

    Only the exact lower-case canonical values are accepted. Missing, null, case variants,
    booleans, numbers, arrays, objects and unknown strings are rejected with a safe ``audience``
    field error so no published consultation can be created with an implicit audience.
    """
    if value is None:
        return None, AUDIENCE_MISSING_MESSAGE
    if value == PUBLIC:
        return PUBLIC, None
    if value == PRIVATE:
        return PRIVATE, None
    return None, AUDIENCE_INVALID_MESSAGE
