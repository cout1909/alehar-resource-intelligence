import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def settings(path, **overrides):
    return Settings(database_url=f"sqlite:///{path.as_posix()}", public_demo_mode=True,
                    public_demo_snapshot=True, scheduler_enabled=True, **overrides)


def test_snapshot_restores_after_loss_and_is_idempotent(tmp_path):
    database = tmp_path / "ephemeral.db"
    expected = None
    for run in range(3):
        if run == 2:
            database.unlink()  # Simulate provider losing disposable state.
        with TestClient(create_app(settings(database))) as client:
            assert client.get("/health").status_code == 200
            lenders = client.get("/lenders").json()
            results = client.get("/verification-results").json()
            assert lenders["total"] == len(results) == 8
            assert all(row["alehar_url"] for row in lenders["lenders"])
            assert sum(row["status"] == "VERIFIED" for row in results) == 7
            assert sum(row["status"] == "REVIEW_REQUIRED" for row in results) == 1
            assert all(row["review_note"] is None for row in results)
            assert all(row["checked_at"].startswith("2026-10-05") for row in results)
            assert client.get("/system/status").json()["scheduler_enabled"] is False
            assert client.post("/verify-all").status_code == 403
            if expected is not None:
                assert results == expected
            expected = results


def test_snapshot_never_overwrites_local_data(tmp_path):
    database = tmp_path / "local.db"
    with TestClient(create_app(Settings(database_url=f"sqlite:///{database.as_posix()}"))) as client:
        before = client.get("/lenders").json()
    with pytest.raises(ValueError, match="existing data was preserved"):
        with TestClient(create_app(settings(database))):
            pass
    with TestClient(create_app(Settings(database_url=f"sqlite:///{database.as_posix()}"))) as client:
        assert client.get("/lenders").json() == before


def test_snapshot_requires_read_only_mode():
    with pytest.raises(ValidationError, match="requires PUBLIC_DEMO_MODE"):
        Settings(public_demo_snapshot=True)
