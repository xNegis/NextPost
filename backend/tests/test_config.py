import pytest

from app.config import get_settings

_CONFIG_KEYS = (
    "CONSULTATION_MIN_PHOTOS",
    "CONSULTATION_MAX_PHOTOS",
    "MAX_OPEN_CONSULTATIONS",
    "PHOTO_MAX_INPUT_BYTES",
    "PHOTO_MAX_PIXELS",
    "PHOTO_MAX_OUTPUT_EDGE",
    "PHOTO_STORAGE_ROOT",
    "PHOTO_LEASE_SECONDS",
    "PHOTO_CLEANUP_INTERVAL_SECONDS",
    "PHOTO_DELETION_ALERT_SECONDS",
    "CONSULTATION_QUESTION_MAX_LENGTH",
    "CONSULTATION_CONTEXT_MAX_LENGTH",
    "PRIVATE_LINK_SECRET",
    "APP_ENV",
)


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    for key in _CONFIG_KEYS:
        monkeypatch.delenv(key, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_match_accepted_values() -> None:
    settings = get_settings()

    assert settings.consultation_min_photos == 2
    assert settings.consultation_max_photos == 10
    assert settings.max_open_consultations == 3
    assert settings.photo_max_input_bytes == 15728640
    assert settings.photo_max_pixels == 40000000
    assert settings.photo_max_output_edge == 2560
    assert settings.photo_lease_seconds == 86400
    assert settings.photo_cleanup_interval_seconds == 3600
    assert settings.photo_deletion_alert_seconds == 86400
    assert settings.consultation_question_max_length == 120
    assert settings.consultation_context_max_length == 500


def test_valid_overrides_are_applied(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MIN_PHOTOS", "3")
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "8")
    monkeypatch.setenv("MAX_OPEN_CONSULTATIONS", "5")
    monkeypatch.setenv("PHOTO_MAX_INPUT_BYTES", "1234")
    monkeypatch.setenv("CONSULTATION_QUESTION_MAX_LENGTH", "200")
    monkeypatch.setenv("CONSULTATION_CONTEXT_MAX_LENGTH", "800")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.consultation_min_photos == 3
    assert settings.consultation_max_photos == 8
    assert settings.max_open_consultations == 5
    assert settings.photo_max_input_bytes == 1234
    assert settings.consultation_question_max_length == 200
    assert settings.consultation_context_max_length == 800


def test_max_below_min_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MIN_PHOTOS", "8")
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "4")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CONSULTATION_MAX_PHOTOS"):
        get_settings()


def test_min_below_two_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MIN_PHOTOS", "1")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CONSULTATION_MIN_PHOTOS"):
        get_settings()


def test_max_below_five_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "4")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CONSULTATION_MAX_PHOTOS"):
        get_settings()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("PHOTO_MAX_INPUT_BYTES", "0"),
        ("PHOTO_MAX_PIXELS", "-1"),
        ("PHOTO_MAX_OUTPUT_EDGE", "0"),
        ("PHOTO_LEASE_SECONDS", "0"),
        ("PHOTO_CLEANUP_INTERVAL_SECONDS", "0"),
        ("PHOTO_DELETION_ALERT_SECONDS", "-5"),
        ("MAX_OPEN_CONSULTATIONS", "0"),
    ],
)
def test_non_positive_resource_values_are_rejected(monkeypatch, key: str, value: str) -> None:
    monkeypatch.setenv(key, value)
    get_settings.cache_clear()

    with pytest.raises(ValueError):
        get_settings()


def test_non_integer_values_are_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PHOTO_MAX_PIXELS", "not-a-number")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PHOTO_MAX_PIXELS"):
        get_settings()


def test_question_max_below_default_length_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_QUESTION_MAX_LENGTH", "26")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CONSULTATION_QUESTION_MAX_LENGTH"):
        get_settings()


def test_context_max_non_positive_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_CONTEXT_MAX_LENGTH", "0")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="CONSULTATION_CONTEXT_MAX_LENGTH"):
        get_settings()


def test_empty_storage_root_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PHOTO_STORAGE_ROOT", "   ")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PHOTO_STORAGE_ROOT"):
        get_settings()


def test_private_link_secret_defaults_in_development() -> None:
    settings = get_settings()
    assert settings.private_link_secret == "nextpost-private-link-secret-local-only"


def test_private_link_secret_requires_value_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PRIVATE_LINK_SECRET"):
        get_settings()


def test_private_link_secret_rejects_short_secret(monkeypatch) -> None:
    monkeypatch.setenv("PRIVATE_LINK_SECRET", "too-short")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PRIVATE_LINK_SECRET"):
        get_settings()


def test_private_link_secret_rejects_local_default_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PRIVATE_LINK_SECRET", "nextpost-private-link-secret-local-only")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PRIVATE_LINK_SECRET"):
        get_settings()


def test_private_link_secret_accepts_strong_secret(monkeypatch) -> None:
    monkeypatch.setenv("PRIVATE_LINK_SECRET", "x" * 32)
    get_settings.cache_clear()

    assert get_settings().private_link_secret == "x" * 32


def test_private_link_secret_accepts_strong_secret_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PRIVATE_LINK_SECRET", "y" * 40)
    get_settings.cache_clear()

    assert get_settings().private_link_secret == "y" * 40


def test_private_link_secret_accepts_local_default_in_development(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PRIVATE_LINK_SECRET", "nextpost-private-link-secret-local-only")
    get_settings.cache_clear()

    assert get_settings().private_link_secret == "nextpost-private-link-secret-local-only"
