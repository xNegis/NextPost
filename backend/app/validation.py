import re

EMAIL_MAX_LENGTH = 320
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

ALIAS_MIN_LENGTH = 3
ALIAS_MAX_LENGTH = 30
ALIAS_PATTERN = re.compile(r"[A-Za-z0-9._]{3,30}")
ALIAS_HAS_ALNUM = re.compile(r"[A-Za-z0-9]")

PASSWORD_MIN_LENGTH = 15
PASSWORD_MAX_LENGTH = 128

RESERVED_ALIASES = frozenset({"admin", "support", "nextpost"})


def canonical_email(raw: str) -> str:
    return raw.strip().casefold()


def validate_email(raw: str) -> str:
    email = canonical_email(raw)
    if not email:
        raise ValueError("Enter an email address.")
    if len(email) > EMAIL_MAX_LENGTH:
        raise ValueError("The email address is too long.")
    if EMAIL_PATTERN.fullmatch(email) is None:
        raise ValueError("Enter a valid email address.")
    return email


def canonical_alias(raw: str) -> str:
    return raw.strip().casefold()


def validate_alias(raw: str) -> tuple[str, str]:
    display = raw.strip()
    canonical = canonical_alias(raw)
    if ALIAS_PATTERN.fullmatch(display) is None:
        raise ValueError(
            "The alias must be between 3 and 30 characters and can only contain "
            "letters, numbers, periods, or underscores."
        )
    if ALIAS_HAS_ALNUM.search(display) is None:
        raise ValueError("The alias must include at least one letter or number.")
    if canonical in RESERVED_ALIASES:
        raise ValueError("That alias is not available.")
    return display, canonical


def validate_password(raw: str) -> str:
    length = len(raw)
    if length < PASSWORD_MIN_LENGTH:
        raise ValueError("The password must be at least 15 characters.")
    if length > PASSWORD_MAX_LENGTH:
        raise ValueError("The password must be at most 128 characters.")
    return raw
