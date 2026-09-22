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


def test_valid_overrides_are_applied(monkeypatch) -> None:
    monkeypatch.setenv("CONSULTATION_MIN_PHOTOS", "3")
    monkeypatch.setenv("CONSULTATION_MAX_PHOTOS", "8")
    monkeypatch.setenv("MAX_OPEN_CONSULTATIONS", "5")
    monkeypatch.setenv("PHOTO_MAX_INPUT_BYTES", "1234")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.consultation_min_photos == 3
    assert settings.consultation_max_photos == 8
    assert settings.max_open_consultations == 5
    assert settings.photo_max_input_bytes == 1234


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


def test_empty_storage_root_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("PHOTO_STORAGE_ROOT", "   ")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="PHOTO_STORAGE_ROOT"):
        get_settings()
