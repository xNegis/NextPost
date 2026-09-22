from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.health import require_database
from app.main import app


def test_liveness_does_not_require_the_database() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_succeeds_when_database_probe_succeeds() -> None:
    app.dependency_overrides[require_database] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.get("/api/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_an_unavailable_database() -> None:
    def unavailable() -> None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    app.dependency_overrides[require_database] = unavailable
    try:
        with TestClient(app) as client:
            response = client.get("/api/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
