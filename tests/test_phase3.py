import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.config import Settings
from app.database.models import Lender, VerificationResult
from app.main import create_app
from app.services.batch import verify_batch
from app.services.scheduler import scheduled_verification
from app.services.source_fetcher import FetchResult
from app.services.verification_service import verify_lender
from scripts.seed_alehar_demo import DATASET, import_dataset


@pytest.fixture
def public_client(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'public.db'}",
                              public_demo_mode=True, scheduler_enabled=True, enable_docs=False,
                              allowed_origins="https://demo.example, https://preview.example"))
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize("path", ["/verify-all", "/lenders/1/verify",
                                   "/verification-results/1/approve", "/verification-results/1/reject"])
def test_public_mutations_blocked_before_database_or_provider(public_client, path):
    with public_client.app.state.session_factory() as session:
        before = session.scalar(select(func.count()).select_from(VerificationResult))
    response = public_client.post(path, json={"note": "must not save"}, headers={"Origin": "https://demo.example"})
    assert response.status_code == 403
    assert response.json()["detail"] == "This action is disabled in the public demo."
    assert response.headers["access-control-allow-origin"] == "https://demo.example"
    with public_client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(VerificationResult)) == before


@pytest.mark.parametrize("path", ["/health", "/lenders", "/lenders/1", "/dashboard/summary",
                                   "/dashboard/latest", "/reviews/pending", "/verification-results", "/system/status"])
def test_public_reads_available(public_client, path):
    assert public_client.get(path).status_code == 200


def test_public_scheduler_and_service_entrypoints_disabled(public_client):
    state = public_client.app.state
    assert state.scheduler is None
    assert public_client.get("/system/status").json()["public_demo_mode"] is True
    scheduled_verification(SimpleNamespace(state=SimpleNamespace(settings=state.settings)))
    with pytest.raises(PermissionError):
        verify_lender(None, 1, state.settings)
    with pytest.raises(PermissionError):
        verify_batch(None, state.settings)


def test_docs_and_cors(public_client):
    for path in ["/docs", "/redoc", "/openapi.json"]:
        assert public_client.get(path).status_code == 404
    assert "access-control-allow-origin" not in public_client.get("/health", headers={"Origin": "https://evil.example"}).headers
    assert public_client.options("/verify-all", headers={"Origin": "https://demo.example", "Access-Control-Request-Method": "POST"}).status_code == 200


@pytest.mark.parametrize("origin", ["*", "https://*.example", "https://example/path", "https://user:pass@example", "file:///tmp", "https://example?x=y"])
def test_invalid_cors_rejected(origin):
    with pytest.raises(ValidationError):
        Settings(allowed_origins=origin)


def test_unexpected_errors_are_sanitized(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'error.db'}", app_env="production"))
    @app.get("/test-failure")
    def fail():
        raise RuntimeError("private filesystem path and secret detail")
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-failure")
        assert response.status_code == 500
        assert "private" not in response.text
        assert response.json()["detail"] == "The request could not be completed."


def test_curated_import_is_idempotent_and_preserves_existing(client):
    records = json.loads(DATASET.read_text(encoding="utf-8"))
    with client.app.state.session_factory() as session:
        result = verify_lender(session, 1, client.app.state.settings,
                               fetcher=lambda url: FetchResult(url, url, error="Test-only source failure"))
        saved_id = result.id
        original_ids = set(session.scalars(select(Lender.id)))
        counts = import_dataset(session, records)
        assert counts["added"] == 4 and counts["updated"] == 4
        assert original_ids.issubset(set(session.scalars(select(Lender.id))))
        second = import_dataset(session, records)
        assert second == {"added": 0, "updated": 0, "unchanged": 8, "skipped": 0}
        assert session.get(VerificationResult, saved_id).review_status.value == "PENDING"
        lender = session.scalar(select(Lender).where(Lender.name == records[0]["name"]))
        lender.is_demo = False
        lender.description = "User-maintained data"
        session.commit()
        assert import_dataset(session, records)["skipped"] == 1
        assert lender.description == "User-maintained data"
    response = client.get("/lenders/1").json()
    assert response["retrieved_at"].endswith("Z")
    assert response["alehar_url"].startswith("https://www.alehar.com/")


def test_dataset_has_bounded_public_fields():
    records = json.loads(DATASET.read_text(encoding="utf-8"))
    assert 8 <= len(records) <= 12
    assert len({row["name"] for row in records}) == len(records)
    for row in records:
        assert row["description"] is None
        assert row["verification_source_url"].startswith("https://")
        assert row["source_notes"] and row["retrieved_at"]
        assert not {"loan_amount", "interest_rate", "products", "regulatory_status"}.intersection(row)
