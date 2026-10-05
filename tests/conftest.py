import socket

import pytest
import requests
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.models import Lender, SourceType
from app.main import create_app


@pytest.fixture(autouse=True)
def prohibit_live_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Tests must not access the live network")

    monkeypatch.setattr(requests.Session, "get", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def app(tmp_path):
    return create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
            verify_all_delay=0,
        )
    )


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def lender():
    return Lender(
        id=1,
        name="Acme Finance Private Limited",
        country="India",
        lender_type="Demo",
        description="Seed record for verification demonstration.",
        website_url="https://acme.example/",
        verification_source_url="https://acme.example/",
        source_type=SourceType.OFFICIAL_WEBSITE,
    )
