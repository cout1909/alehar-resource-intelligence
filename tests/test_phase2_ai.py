from unittest.mock import Mock

import httpx
import pytest

from app.core.config import Settings
from app.services import verification_service
from app.services.ai import service
from app.services.ai.analyzer import analyze_source
from app.services.ai.extractor import extract_source
from app.services.comparator import compare_lender
from app.services.source_fetcher import FetchResult
from app.services.text_extractor import PageData
from tests.test_verification import success

EXTRACTION = {
    "company_name": "Acme Finance",
    "company_description": None,
    "entity_type": None,
    "products_or_services": [],
    "geographies": [],
    "identity_evidence": ["Acme Finance"],
    "uncertain_fields": [],
    "source_summary": "Acme Finance public information.",
}
ANALYSIS = {
    "identity_match": True,
    "possible_mismatch": False,
    "review_recommended": False,
    "reason": "Basic identity appears consistent.",
    "supported_findings": ["Name present"],
    "uncertain_findings": [],
}


def configured(**changes):
    return Settings(
        **{
            "ai_enabled": True,
            "groq_api_key": "test-placeholder-only",
            "ai_model": "mock-model",
            **changes,
        }
    )


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"ai_enabled": False}, "disabled"),
        ({"groq_api_key": ""}, "not_configured"),
        ({"ai_model": ""}, "not_configured"),
        ({"ai_model": "  "}, "not_configured"),
        ({"ai_provider": "unsupported"}, "unavailable"),
    ],
)
def test_disabled_or_missing_config_never_initializes_provider(
    changes, expected, lender, monkeypatch
):
    factory = Mock(side_effect=AssertionError("Must not initialize AI"))
    monkeypatch.setattr(service, "create_client", factory)
    outcome = service.enrich_verification(configured(**changes), lender, None, None)
    assert outcome.status == expected
    factory.assert_not_called()


def test_structured_extraction_and_analysis(lender):
    page = PageData(
        "Acme Finance",
        "",
        "Acme Finance provides public business information for visitors.",
    )
    client = Mock()
    client.with_structured_output.return_value.invoke.side_effect = [
        EXTRACTION,
        ANALYSIS,
    ]
    extraction = extract_source(client, page, 12000)
    analysis = analyze_source(
        client, lender, compare_lender(lender, page, lender.website_url), extraction
    )
    assert extraction.company_name == "Acme Finance"
    assert analysis.identity_match
    assert client.with_structured_output.call_count == 2
    assert client.with_structured_output.call_args.kwargs["method"] == "function_calling"


def test_fabricated_quote_is_rejected():
    client = Mock()
    client.with_structured_output.return_value.invoke.return_value = EXTRACTION
    with pytest.raises(ValueError, match="Unsupported evidence"):
        extract_source(client, PageData("Other", "", "Nothing related"), 12000)


def test_ai_cannot_claim_omitted_description_matches(lender):
    from app.schemas.ai import SourceIntelligence
    lender.description = ""
    page = PageData("Acme Finance", "", "Acme Finance public source information")
    client = Mock()
    client.with_structured_output.return_value.invoke.return_value = {
        **ANALYSIS, "supported_findings": ["Description matches"]}
    with pytest.raises(ValueError, match="omitted description"):
        analyze_source(client, lender, compare_lender(lender, page, lender.website_url),
                       SourceIntelligence.model_validate(EXTRACTION))


@pytest.mark.parametrize(
    "failure",
    [
        "timeout",
        "rate_limit",
        "authentication",
        "provider",
        "malformed",
        "initialization",
    ],
)
def test_provider_failures_preserve_deterministic_result(client, app, monkeypatch, failure):
    from groq import APIStatusError, AuthenticationError, RateLimitError

    app.state.settings = configured(database_url=app.state.settings.database_url)
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    exceptions = {
        "timeout": httpx.ReadTimeout("private provider detail"),
        "rate_limit": RateLimitError(
            "private provider detail",
            response=httpx.Response(429, request=request),
            body=None,
        ),
        "authentication": AuthenticationError(
            "private provider detail",
            response=httpx.Response(401, request=request),
            body=None,
        ),
        "provider": APIStatusError(
            "private provider detail",
            response=httpx.Response(503, request=request),
            body=None,
        ),
        "initialization": RuntimeError("private provider detail"),
    }
    fake = Mock()
    if failure == "malformed":
        fake.with_structured_output.return_value.invoke.return_value = {"company_name": 123}
    else:
        fake.with_structured_output.return_value.invoke.side_effect = exceptions[failure]
    factory = Mock(return_value=fake)
    if failure == "initialization":
        factory.side_effect = exceptions[failure]
    monkeypatch.setattr(service, "create_client", factory)
    monkeypatch.setattr(verification_service, "fetch_source", success)
    response = client.post("/lenders/1/verify")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "VERIFIED"
    assert result["confidence_score"] == 100
    assert result["ai_status"] == "unavailable"
    assert result["ai_analysis"] is None
    assert "private provider detail" not in response.text
    assert "test-placeholder-only" not in response.text
    if failure == "rate_limit":
        assert "rate limit" in result["ai_error"]
    if failure == "timeout":
        assert "time limit" in result["ai_error"]
    assert client.get("/system/status").json()["ai_status"] == "unavailable"


def test_ai_can_add_review_but_not_change_confidence_or_lender(client, app, monkeypatch):
    app.state.settings = configured(database_url=app.state.settings.database_url)
    fake = Mock()
    fake.with_structured_output.return_value.invoke.side_effect = [
        {**EXTRACTION, "company_name": "HDFC Bank", "identity_evidence": ["HDFC Bank"]},
        {**ANALYSIS, "review_recommended": True, "reason": "Human review recommended."},
    ]
    monkeypatch.setattr(service, "create_client", Mock(return_value=fake))
    monkeypatch.setattr(verification_service, "fetch_source", success)
    before = client.get("/lenders/1").json()
    result = client.post("/lenders/1/verify").json()
    assert result["ai_status"] == "success"
    assert result["ai_model"] == "mock-model"
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["review_status"] == "PENDING"
    assert result["confidence_score"] == 100
    assert "NO_CHANGE" not in {change["type"] for change in result["detected_changes"]}
    after = client.get("/lenders/1").json()
    assert {k: v for k, v in after.items() if k != "last_verified_at"} == {
        k: v for k, v in before.items() if k != "last_verified_at"
    }


def test_ai_cannot_clear_deterministic_concern(client, app, monkeypatch):
    app.state.settings = configured(database_url=app.state.settings.database_url)
    fake = Mock()
    fake.with_structured_output.return_value.invoke.side_effect = [
        {**EXTRACTION, "identity_evidence": []},
        ANALYSIS,
    ]
    monkeypatch.setattr(service, "create_client", Mock(return_value=fake))
    monkeypatch.setattr(
        verification_service,
        "fetch_source",
        lambda url, settings: FetchResult(
            url,
            "https://other.example/",
            200,
            True,
            "text/html",
            "<title>HDFC Bank</title><p>HDFC Bank public information on a mismatching domain.</p>",
        ),
    )
    result = client.post("/lenders/1/verify").json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["confidence_score"] == 60


def test_settings_do_not_serialize_key():
    settings = configured()
    assert "test-placeholder-only" not in repr(settings)
    assert "groq_api_key" not in settings.model_dump()
