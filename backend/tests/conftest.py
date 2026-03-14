import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import database, file_manager, rate_limiter
from app.services.auth_service import get_api_key_registry


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FORENSICLEAR_API_KEYS", "analyst:test-key,reviewer:review-key")
    monkeypatch.setenv("FORENSICLEAR_WORKER_COUNT", "1")
    monkeypatch.setenv("FORENSICLEAR_QUEUE_MAX_SIZE", "4")
    get_api_key_registry.cache_clear()

    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "forensiclear.db")
    monkeypatch.setattr(file_manager, "UPLOADS_DIR", tmp_path / "uploads")
    monkeypatch.setattr(file_manager, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(file_manager, "LOGS_DIR", tmp_path / "logs")

    rate_limiter._buckets["upload"].clear()
    rate_limiter._buckets["process"].clear()

    file_manager.ensure_storage_dirs()
    database.init_db()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-key"}


@pytest.fixture()
def other_auth_headers():
    return {"Authorization": "Bearer review-key"}
