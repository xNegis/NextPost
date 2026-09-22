import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _parse_origins(raw: str) -> tuple[str, ...]:
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    if not origins:
        raise ValueError("CORS_ORIGINS must contain at least one origin")
    return origins


def _require_int(name: str, raw: str | None, default: int, minimum: int | None) -> int:
    if raw is None or raw.strip() == "":
        value = default
    else:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer") from exc
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    cors_origins: tuple[str, ...]
    session_secret: str
    consultation_min_photos: int
    consultation_max_photos: int
    max_open_consultations: int
    photo_max_input_bytes: int
    photo_max_pixels: int
    photo_max_output_edge: int
    photo_storage_root: Path
    photo_lease_seconds: int
    photo_cleanup_interval_seconds: int
    photo_deletion_alert_seconds: int

    def __post_init__(self) -> None:
        if self.consultation_min_photos < 2:
            raise ValueError("CONSULTATION_MIN_PHOTOS must be at least 2")
        if self.consultation_max_photos < self.consultation_min_photos:
            raise ValueError("CONSULTATION_MAX_PHOTOS must not be below CONSULTATION_MIN_PHOTOS")
        if self.consultation_max_photos < 5:
            raise ValueError("CONSULTATION_MAX_PHOTOS must support at least 5")
        if self.max_open_consultations < 1:
            raise ValueError("MAX_OPEN_CONSULTATIONS must be positive")
        if self.photo_max_input_bytes < 1:
            raise ValueError("PHOTO_MAX_INPUT_BYTES must be positive")
        if self.photo_max_pixels < 1:
            raise ValueError("PHOTO_MAX_PIXELS must be positive")
        if self.photo_max_output_edge < 1:
            raise ValueError("PHOTO_MAX_OUTPUT_EDGE must be positive")
        if self.photo_lease_seconds < 1:
            raise ValueError("PHOTO_LEASE_SECONDS must be positive")
        if self.photo_cleanup_interval_seconds < 1:
            raise ValueError("PHOTO_CLEANUP_INTERVAL_SECONDS must be positive")
        if self.photo_deletion_alert_seconds < 1:
            raise ValueError("PHOTO_DELETION_ALERT_SECONDS must be positive")
        if not self.photo_storage_root:
            raise ValueError("PHOTO_STORAGE_ROOT must be set")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    storage_root = os.getenv("PHOTO_STORAGE_ROOT", "data/photos").strip()
    if not storage_root:
        raise ValueError("PHOTO_STORAGE_ROOT must be set")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://nextpost:nextpost-local-only@localhost:5432/nextpost",
        ),
        cors_origins=_parse_origins(
            os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:4173")
        ),
        session_secret=os.getenv("SESSION_SECRET", "nextpost-session-secret-local-only"),
        consultation_min_photos=_require_int(
            "CONSULTATION_MIN_PHOTOS", os.getenv("CONSULTATION_MIN_PHOTOS"), 2, 2
        ),
        consultation_max_photos=_require_int(
            "CONSULTATION_MAX_PHOTOS", os.getenv("CONSULTATION_MAX_PHOTOS"), 10, 2
        ),
        max_open_consultations=_require_int(
            "MAX_OPEN_CONSULTATIONS", os.getenv("MAX_OPEN_CONSULTATIONS"), 3, 1
        ),
        photo_max_input_bytes=_require_int(
            "PHOTO_MAX_INPUT_BYTES", os.getenv("PHOTO_MAX_INPUT_BYTES"), 15728640, 1
        ),
        photo_max_pixels=_require_int(
            "PHOTO_MAX_PIXELS", os.getenv("PHOTO_MAX_PIXELS"), 40000000, 1
        ),
        photo_max_output_edge=_require_int(
            "PHOTO_MAX_OUTPUT_EDGE", os.getenv("PHOTO_MAX_OUTPUT_EDGE"), 2560, 1
        ),
        photo_storage_root=Path(storage_root),
        photo_lease_seconds=_require_int(
            "PHOTO_LEASE_SECONDS", os.getenv("PHOTO_LEASE_SECONDS"), 86400, 1
        ),
        photo_cleanup_interval_seconds=_require_int(
            "PHOTO_CLEANUP_INTERVAL_SECONDS",
            os.getenv("PHOTO_CLEANUP_INTERVAL_SECONDS"),
            3600,
            1,
        ),
        photo_deletion_alert_seconds=_require_int(
            "PHOTO_DELETION_ALERT_SECONDS",
            os.getenv("PHOTO_DELETION_ALERT_SECONDS"),
            86400,
            1,
        ),
    )
