from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account
from app.security import hash_password, verify_password
from app.validation import validate_alias, validate_email, validate_password

EMAIL_CONSTRAINT = "uq_accounts_email"
ALIAS_CONSTRAINT = "uq_accounts_alias_canonical"

_DUMMY_HASH = hash_password("nextpost-timing-equalisation-password")


class DuplicateEmailError(Exception):
    """Raised when the canonical email is already registered."""


class DuplicateAliasError(Exception):
    """Raised when the canonical alias is already taken."""


def _failed_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    constraint_name = getattr(diag, "constraint_name", None) if diag is not None else None
    if isinstance(constraint_name, str) and constraint_name:
        return constraint_name

    message = str(exc.orig)
    if f"accounts.{Account.email.key}" in message:
        return EMAIL_CONSTRAINT
    if f"accounts.{Account.alias_canonical.key}" in message:
        return ALIAS_CONSTRAINT
    return None


def register_account(session: Session, email: str, alias: str, password: str) -> Account:
    canonical_email = validate_email(email)
    display_alias, canonical_alias = validate_alias(alias)
    validated_password = validate_password(password)
    account = Account(
        email=canonical_email,
        alias=display_alias,
        alias_canonical=canonical_alias,
        password_hash=hash_password(validated_password),
    )
    session.add(account)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = _failed_constraint(exc)
        if constraint == EMAIL_CONSTRAINT:
            raise DuplicateEmailError from exc
        if constraint == ALIAS_CONSTRAINT:
            raise DuplicateAliasError from exc
        raise
    return account


def authenticate_account(session: Session, email: str, password: str) -> Account | None:
    canonical_email = validate_email(email)
    account = session.scalar(select(Account).where(Account.email == canonical_email))
    if account is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, account.password_hash):
        return None
    return account
