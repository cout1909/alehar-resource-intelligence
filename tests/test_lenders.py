import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.lender import LenderCreate


def test_list_and_detail(client):
    response = client.get("/lenders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 8
    assert all(item["is_demo"] and item["alehar_url"] is None for item in data["lenders"])
    detail = client.get("/lenders/1")
    assert detail.status_code == 200
    assert detail.json() == data["lenders"][0]
    assert detail.json()["created_at"].endswith("Z")


@pytest.mark.parametrize("path", ["/lenders/999", "/verification-results/999"])
def test_not_found(client, path):
    assert client.get(path).status_code == 404


def test_verify_missing(client):
    assert client.post("/lenders/999/verify").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/lenders/0",
        "/lenders/nope",
        "/verification-results?limit=0",
        "/verification-results?offset=-1",
    ],
)
def test_invalid_parameters(client, path):
    assert client.get(path).status_code == 422


def test_restart_does_not_duplicate_seed(app):
    with TestClient(app) as client:
        first = client.get("/lenders").json()
    with TestClient(app) as client:
        assert client.get("/lenders").json() == first


def test_import_schema_rejects_bad_url():
    with pytest.raises(ValidationError):
        LenderCreate(
            name="Acme",
            country="India",
            lender_type="Demo",
            description="Demo",
            website_url="file:///etc/passwd",
        )
