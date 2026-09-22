import pytest
from sqlalchemy import delete, func, select

from app.accounts_service import DuplicateEmailError, register_account
from app.models import Account

VALID_PASSWORD = "correct-horse-battery-staple"


def register(client, email="ana@example.com", alias="Ana", password=VALID_PASSWORD):
    return client.post(
        "/api/accounts",
        json={"email": email, "alias": alias, "password": password},
    )


def sign_in(client, email="ana@example.com", password=VALID_PASSWORD):
    return client.post("/api/session", json={"email": email, "password": password})


def test_registration_creates_account_and_session(client) -> None:
    response = register(client, email="  Ana@Example.COM ", alias="Ana")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "alias"}
    assert body["alias"] == "Ana"

    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()
    assert "max-age" not in set_cookie.lower()

    session_response = client.get("/api/session")
    assert session_response.status_code == 200
    assert session_response.json() == {
        "authenticated": True,
        "account": {"id": body["id"], "alias": "Ana"},
    }


def test_registration_canonicalises_email_and_alias(client, session_factory) -> None:
    response = register(client, email="  Ana@Example.COM ", alias="Ana.Smith")

    assert response.status_code == 201

    with session_factory() as session:
        account = session.scalar(select(Account))
        assert account is not None
        assert account.email == "ana@example.com"
        assert account.alias == "Ana.Smith"
        assert account.alias_canonical == "ana.smith"


def test_password_is_stored_only_as_argon2id_hash(client, session_factory) -> None:
    response = register(client, password=VALID_PASSWORD)
    assert response.status_code == 201

    with session_factory() as session:
        account = session.scalar(select(Account))
        assert account is not None
        assert account.password_hash != VALID_PASSWORD
        assert account.password_hash.startswith("$argon2id$")


def test_duplicate_email_is_generic_and_non_enumerating(client) -> None:
    assert register(client, email="ana@example.com", alias="Ana").status_code == 201

    response = register(client, email="ANA@example.com", alias="Otra")

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "registration_unavailable"}}


def test_duplicate_alias_is_case_insensitive(client) -> None:
    assert register(client, email="ana@example.com", alias="Ana").status_code == 201

    response = register(client, email="other@example.com", alias="ana")

    assert response.status_code == 409
    assert response.json() == {"detail": {"code": "alias_unavailable"}}


def test_invalid_email_returns_field_error(client) -> None:
    response = register(client, email="not-an-email", alias="Ana")

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "validation_error"
    assert "email" in body["detail"]["field_errors"]


def test_invalid_alias_returns_field_error(client) -> None:
    response = register(client, email="ana@example.com", alias="ab")

    assert response.status_code == 422
    assert "alias" in response.json()["detail"]["field_errors"]


def test_reserved_alias_is_rejected(client) -> None:
    response = register(client, email="ana@example.com", alias="Admin")

    assert response.status_code == 422
    assert "alias" in response.json()["detail"]["field_errors"]


@pytest.mark.parametrize("password", ["a" * 14, "a" * 129])
def test_password_length_boundaries_are_enforced(client, password: str) -> None:
    response = register(client, email="ana@example.com", alias="Ana", password=password)

    assert response.status_code == 422
    assert "password" in response.json()["detail"]["field_errors"]


def test_unicode_password_is_accepted(client) -> None:
    response = register(
        client, email="ana@example.com", alias="Ana", password="cóntraseña-segura-ñ-123"
    )

    assert response.status_code == 201


def test_missing_fields_are_rejected(client) -> None:
    response = client.post("/api/accounts", json={"email": "ana@example.com"})

    assert response.status_code == 422
    field_errors = response.json()["detail"]["field_errors"]
    assert "alias" in field_errors
    assert "password" in field_errors


def test_extra_fields_are_rejected(client) -> None:
    response = client.post(
        "/api/accounts",
        json={
            "email": "ana@example.com",
            "alias": "Ana",
            "password": VALID_PASSWORD,
            "role": "admin",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_session_is_unauthenticated_without_cookie(client) -> None:
    response = client.get("/api/session")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}


def test_session_is_unauthenticated_with_invalid_cookie(client) -> None:
    client.cookies.set("nextpost_session", "not-a-valid-signed-session")

    response = client.get("/api/session")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}


def test_session_is_unauthenticated_when_account_no_longer_exists(client, session_factory) -> None:
    assert register(client).status_code == 201
    with session_factory() as session:
        session.execute(delete(Account))
        session.commit()

    response = client.get("/api/session")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}


def test_registration_rolls_back_on_duplicate_email(session_factory) -> None:
    with session_factory() as session:
        register_account(session, "ana@example.com", "Ana", VALID_PASSWORD)

    with session_factory() as session:
        before = session.scalar(select(func.count()).select_from(Account))
        with pytest.raises(DuplicateEmailError):
            register_account(session, " ANA@EXAMPLE.COM ", "Otra", VALID_PASSWORD)
        after = session.scalar(select(func.count()).select_from(Account))

    assert before == after == 1


def test_login_creates_session_and_returns_account(client) -> None:
    register(client, email="  Ana@Example.COM ", alias="Ana")

    response = sign_in(client, email="ana@EXAMPLE.com")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "alias"}
    assert body["alias"] == "Ana"

    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()

    session_response = client.get("/api/session")
    assert session_response.status_code == 200
    assert session_response.json() == {
        "authenticated": True,
        "account": {"id": body["id"], "alias": "Ana"},
    }


def test_login_canonicalises_email(client) -> None:
    register(client, email="ana@example.com", alias="Ana")

    response = sign_in(client, email="  ANA@EXAMPLE.COM  ")

    assert response.status_code == 200


def test_wrong_password_is_rejected_without_a_session(client) -> None:
    register(client)

    response = sign_in(client, password="not-the-right-password")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_credentials"}}
    assert client.get("/api/session").status_code == 401


def test_unknown_email_is_rejected_like_a_wrong_password(client) -> None:
    register(client)

    response = sign_in(client, email="unknown@example.com")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_credentials"}}


def test_failed_login_clears_an_existing_session(client) -> None:
    register(client)
    assert client.get("/api/session").status_code == 200

    response = sign_in(client, password="not-the-right-password")

    assert response.status_code == 401
    assert client.get("/api/session").status_code == 401


def test_malformed_login_email_is_a_validation_error(client) -> None:
    response = sign_in(client, email="not-an-email")

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "validation_error"
    assert "email" in body["detail"]["field_errors"]


def test_login_extra_fields_are_rejected(client) -> None:
    register(client)

    response = client.post(
        "/api/session",
        json={"email": "ana@example.com", "password": VALID_PASSWORD, "role": "admin"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_login_missing_fields_are_rejected(client) -> None:
    response = client.post("/api/session", json={"email": "ana@example.com"})

    assert response.status_code == 422
    assert "password" in response.json()["detail"]["field_errors"]


def test_malformed_login_clears_an_existing_session(client) -> None:
    register(client)
    assert client.get("/api/session").status_code == 200

    response = client.post("/api/session", json={"email": "not-an-email"})

    assert response.status_code == 422
    assert client.get("/api/session").status_code == 401


def test_invalid_stored_hash_never_authenticates(client, session_factory) -> None:
    register(client)
    with session_factory() as session:
        account = session.scalar(select(Account))
        assert account is not None
        account.password_hash = "not-a-valid-argon2-hash"
        session.commit()

    response = sign_in(client)

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "invalid_credentials"}}


def test_logout_clears_the_session(client) -> None:
    register(client)
    assert client.get("/api/session").status_code == 200

    response = client.delete("/api/session")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/api/session").status_code == 401


def test_logout_without_a_session_is_idempotent(client) -> None:
    response = client.delete("/api/session")

    assert response.status_code == 204
    assert client.get("/api/session").status_code == 401


def test_logout_with_an_invalid_cookie_is_idempotent(client) -> None:
    client.cookies.set("nextpost_session", "not-a-valid-signed-session")

    response = client.delete("/api/session")

    assert response.status_code == 204
    assert client.get("/api/session").status_code == 401


def test_logout_does_not_delete_the_account(client, session_factory) -> None:
    register(client)

    assert client.delete("/api/session").status_code == 204

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Account)) == 1


def test_profile_returns_owner_email_and_nickname(client) -> None:
    assert register(client, email="  Ana@Example.COM ", alias="Ana").status_code == 201

    response = client.get("/api/profile")

    assert response.status_code == 200
    assert response.json() == {"email": "ana@example.com", "nickname": "Ana"}


def test_profile_exposes_only_email_and_nickname(client) -> None:
    assert register(client).status_code == 201

    body = client.get("/api/profile").json()

    assert set(body) == {"email", "nickname"}
    assert "id" not in body
    assert "alias" not in body
    assert "alias_canonical" not in body
    assert "password_hash" not in body
    assert "created_at" not in body


def test_profile_without_a_cookie_is_unauthenticated(client) -> None:
    response = client.get("/api/profile")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}


def test_profile_with_an_invalid_cookie_is_unauthenticated(client) -> None:
    client.cookies.set("nextpost_session", "not-a-valid-signed-session")

    response = client.get("/api/profile")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}


def test_profile_with_a_deleted_account_is_unauthenticated(client, session_factory) -> None:
    assert register(client).status_code == 201
    with session_factory() as session:
        session.execute(delete(Account))
        session.commit()

    response = client.get("/api/profile")

    assert response.status_code == 401
    assert response.json() == {"detail": {"code": "unauthenticated"}}
