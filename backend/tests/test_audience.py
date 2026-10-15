import pytest
from pydantic import ValidationError

from app.audience import (
    AUDIENCE_INVALID_MESSAGE,
    AUDIENCE_MISSING_MESSAGE,
    PRIVATE,
    PUBLIC,
    validate_audience,
)
from app.schemas import ConsultationAudienceRequest


@pytest.mark.parametrize("value", [PUBLIC, PRIVATE])
def test_canonical_values_are_accepted(value: str) -> None:
    assert validate_audience(value) == (value, None)


@pytest.mark.parametrize("value", [None])
def test_missing_audience_is_rejected(value: object) -> None:
    assert validate_audience(value) == (None, AUDIENCE_MISSING_MESSAGE)


@pytest.mark.parametrize(
    "value",
    [
        "Public",
        "PRIVATE",
        "public ",
        " public",
        "unknown",
        "",
        True,
        False,
        0,
        1,
        [],
        {},
        ["public"],
        {"audience": "public"},
    ],
)
def test_invalid_audience_is_rejected(value: object) -> None:
    assert validate_audience(value) == (None, AUDIENCE_INVALID_MESSAGE)


def test_case_variants_are_rejected() -> None:
    assert validate_audience("Public") == (None, AUDIENCE_INVALID_MESSAGE)
    assert validate_audience("PUBLIC") == (None, AUDIENCE_INVALID_MESSAGE)
    assert validate_audience("Private") == (None, AUDIENCE_INVALID_MESSAGE)


def test_reusable_schema_accepts_canonical_audience() -> None:
    assert ConsultationAudienceRequest(audience="public").audience == PUBLIC
    assert ConsultationAudienceRequest(audience="private").audience == PRIVATE


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, AUDIENCE_MISSING_MESSAGE),
        ({"audience": None}, AUDIENCE_MISSING_MESSAGE),
        ({"audience": "Public"}, AUDIENCE_INVALID_MESSAGE),
    ],
)
def test_reusable_schema_returns_safe_audience_error(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ConsultationAudienceRequest.model_validate(payload)

    assert exc_info.value.errors()[0]["loc"] == ("audience",)
    assert exc_info.value.errors()[0]["msg"] == message
