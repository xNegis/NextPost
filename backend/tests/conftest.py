import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["NEXTPOST_RUN_MAINTENANCE"] = "0"

from app.api.photos import get_photo_storage  # noqa: E402
from app.db import Base, get_db_session  # noqa: E402
from app.main import app  # noqa: E402
from app.storage import PhotoStorage  # noqa: E402


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def storage(tmp_path) -> PhotoStorage:
    photo_storage = PhotoStorage(tmp_path / "photos")
    photo_storage.ensure_dirs()
    return photo_storage


@pytest.fixture()
def client(session_factory, storage) -> Generator[TestClient, None, None]:
    def override_db_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    def override_storage() -> PhotoStorage:
        return storage

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_photo_storage] = override_storage
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
