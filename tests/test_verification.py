from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.database.models import Lender, VerificationResult
from app.services import verification_service
from app.services.source_fetcher import FetchResult


def success(url, settings=None):
    return FetchResult(
        url,
        url,
        200,
        True,
        "text/html",
        """
        <title>HDFC Bank</title><main>HDFC Bank welcomes you to its official
        public website. Explore information about the bank and its services.</main>
    """,
    )


def test_success_persistence_and_no_business_edits(client, app, monkeypatch):
    monkeypatch.setattr(verification_service, "fetch_source", success)
    before = client.get("/lenders/1").json()
    response = client.post("/lenders/1/verify", json={"url": "http://localhost/"})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "VERIFIED"
    assert result["confidence_score"] == 100
    assert result["source_url"] == before["verification_source_url"]
    assert result["checked_at"].endswith("Z")
    after = client.get("/lenders/1").json()
    assert after.pop("last_verified_at") is not None
    before.pop("last_verified_at")
    assert after == before
    assert client.get(f"/verification-results/{result['id']}").json() == result
    assert client.get("/verification-results").json() == [result]
    with app.state.session_factory() as session:
        assert session.get(VerificationResult, result["id"]).status == "VERIFIED"


def test_source_unavailable(client, monkeypatch):
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        lambda url, settings: FetchResult(url, url, error="Timed out", error_kind="timeout"),
    )
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["confidence_score"] == 0
    assert result["source_reachable"] is False


def test_missing_source(client, app):
    with app.state.session_factory() as session:
        session.get(Lender, 1).verification_source_url = None
        session.commit()
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["source_url"] is None


def test_unrelated_source_review(client, monkeypatch):
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        lambda url, settings: FetchResult(
            url,
            "https://other.example/",
            200,
            True,
            "text/html",
            "<title>Other Business</title><p>We sell household products unrelated to this lender.</p>",
        ),
    )
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["confidence_score"] < 60


def test_unsupported_source_review(client, monkeypatch):
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        lambda url, settings: FetchResult(
            url,
            url,
            200,
            True,
            "application/pdf",
            error="Unsupported PDF",
            error_kind="unsupported_content",
        ),
    )
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["source_reachable"] is True


def test_internal_error_is_recorded(client, monkeypatch):
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        Mock(side_effect=RuntimeError("test internal failure")),
    )
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "ERROR"
    assert result["confidence_score"] == 0
    assert "test internal failure" not in result["error_message"]
    assert len(client.get("/verification-results").json()) == 1


def test_verify_all_sequential_summary_skips_missing(client, app, monkeypatch):
    with app.state.session_factory() as session:
        lenders = session.scalars(select(Lender).order_by(Lender.id)).all()
        lenders[-1].verification_source_url = None
        session.commit()
        urls = [item.verification_source_url for item in lenders[:-1]]
    fetcher = Mock(
        side_effect=[
            success(urls[0]),
            FetchResult(urls[1], urls[1], 200, True, "text/html", "<title>Other company</title>"),
            FetchResult(urls[2], urls[2], error="Connection failed"),
            RuntimeError("processing failed"),
            FetchResult(urls[4], urls[4], error="Connection failed"),
            FetchResult(urls[5], urls[5], error="Connection failed"),
            FetchResult(urls[6], urls[6], error="Connection failed"),
        ]
    )
    monkeypatch.setattr(verification_service, "fetch_source", fetcher)
    response = client.post("/verify-all")
    assert response.status_code == 200
    assert response.json() == {
        "total": 7,
        "verified": 1,
        "review_required": 1,
        "source_unavailable": 4,
        "errors": 1,
    }
    assert [call.args[0] for call in fetcher.call_args_list] == urls
    assert len(client.get("/verification-results").json()) == 7


def test_concurrent_trigger_returns_conflict(client, app):
    with app.state.verification_lock:
        assert client.post("/verify-all").status_code == 409
        assert client.post("/lenders/1/verify").status_code == 409


def test_history_survives_app_restart(app, monkeypatch):
    monkeypatch.setattr(verification_service, "fetch_source", success)
    with TestClient(app) as client:
        first = client.post("/lenders/1/verify").json()
        second = client.post("/lenders/1/verify").json()
    with TestClient(app) as client:
        assert client.get("/verification-results?limit=1").json() == [second]
        assert client.get("/verification-results?limit=1&offset=1").json() == [first]


def test_database_failure_does_not_claim_saved_result(client, app, monkeypatch):
    monkeypatch.setattr(verification_service, "fetch_source", success)
    with app.state.session_factory() as session:
        session_class = type(session)
    monkeypatch.setattr(
        session_class,
        "commit",
        Mock(side_effect=OperationalError("commit", {}, Exception("test failure"))),
    )
    response = client.post("/lenders/1/verify")
    assert response.status_code == 503
    assert not app.state.verification_lock.locked()
