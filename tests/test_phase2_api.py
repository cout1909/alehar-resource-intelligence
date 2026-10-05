import pytest

from app.services import verification_service
from app.services.source_fetcher import FetchResult
from tests.test_verification import success


def pending(client, monkeypatch, lender_id=1):
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        lambda url, settings: FetchResult(url, url, error="Unavailable"),
    )
    return client.post(f"/lenders/{lender_id}/verify").json()


@pytest.mark.parametrize("action,status", [("approve", "APPROVED"), ("reject", "REJECTED")])
def test_review_decisions_do_not_edit_lender(client, monkeypatch, action, status):
    result = pending(client, monkeypatch)
    before = client.get("/lenders/1").json()
    queue = client.get("/reviews/pending").json()
    assert queue[0]["lender_name"] == "HDFC Bank"
    reviewed = client.post(
        f"/verification-results/{result['id']}/{action}",
        json={"note": "Checked manually"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == status
    assert reviewed.json()["status"] == result["status"]
    assert reviewed.json()["review_note"] == "Checked manually"
    assert reviewed.json()["reviewed_at"].endswith("Z")
    assert client.get("/reviews/pending").json() == []
    assert client.get("/lenders/1").json() == before
    assert client.post(f"/verification-results/{result['id']}/{action}", json={}).status_code == 409


def test_review_validation(client, monkeypatch):
    result = pending(client, monkeypatch)
    assert client.post("/verification-results/999/approve", json={}).status_code == 404
    assert (
        client.post(
            f"/verification-results/{result['id']}/approve", json={"note": "a" * 2001}
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/verification-results/{result['id']}/approve",
            json={"note": "okay", "status": "VERIFIED"},
        ).status_code
        == 422
    )


def test_dashboard_uses_latest_lender_status_and_all_review_decisions(client, monkeypatch):
    result = pending(client, monkeypatch)
    client.post(f"/verification-results/{result['id']}/approve", json={})
    monkeypatch.setattr(verification_service, "fetch_source", success)
    verified = client.post("/lenders/1/verify").json()
    summary = client.get("/dashboard/summary").json()
    assert summary["total_lenders"] == 8
    assert summary["verified"] == 1
    assert summary["source_unavailable"] == 0
    assert summary["unverified"] == 7
    assert summary["approved_reviews"] == 1
    assert summary["pending_reviews"] == 0
    assert summary["last_verification_time"].endswith("Z")
    assert client.get("/dashboard/latest").json() == [verified]


def test_history_and_filters(client, monkeypatch):
    first = pending(client, monkeypatch)
    second = pending(client, monkeypatch, 2)
    assert client.get("/lenders/1/history").json() == [first]
    assert client.get("/lenders/999/history").status_code == 404
    assert client.get(
        "/verification-results?lender_id=2&status=SOURCE_UNAVAILABLE&review_status=PENDING"
    ).json() == [second]
    assert client.get("/verification-results?status=INVALID").status_code == 422


def test_system_status_and_cors(client, app):
    result = client.get("/system/status")
    assert result.json()["database_status"] == "connected"
    assert result.json()["ai_status"] == "disabled"
    assert result.json()["scheduler_enabled"] is False
    assert app.state.scheduler is None
    assert "groq_api_key" not in result.text.lower()
    assert "database_url" not in result.text.lower()
    response = client.options(
        "/lenders",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options(
        "/lenders",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers
