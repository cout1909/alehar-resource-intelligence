import pytest

from app.database.models import SourceType, VerificationStatus
from app.services.comparator import compare_lender, domain_matches, name_matches
from app.services.text_extractor import PageData


@pytest.mark.parametrize(
    "name,text",
    [
        ("Acme Finance Private Limited", "Welcome to ACME Finance Ltd."),
        ("UGRO Capital", "U-GRO Capital Limited"),
        ("FlexiLoans", "Flexi Loans: About us"),
        ("Acme Pvt. Ltd.", "ACME"),
    ],
)
def test_company_name_variants(name, text):
    assert name_matches(name, text)


@pytest.mark.parametrize(
    "name,text", [("ICICI", "noticici"), ("SIDBI", "sidbious"), ("", "anything")]
)
def test_name_matching_has_boundaries(name, text):
    assert not name_matches(name, text)


def page(title="Acme Finance"):
    return PageData(
        title,
        "Acme Finance services",
        "Acme Finance provides business services. Contact the team to learn more.",
    )


def test_high_confidence_identity(lender):
    result = compare_lender(lender, page(), "https://www.acme.example/about")
    assert result.status == VerificationStatus.VERIFIED
    assert result.confidence_score == 100
    assert result.detected_changes[0]["type"] == "NO_CHANGE"


def test_domain_mismatch_even_with_name(lender):
    result = compare_lender(lender, page(), "https://acme.example.evil.com/")
    assert result.status == VerificationStatus.REVIEW_REQUIRED
    assert "DOMAIN_MISMATCH" in {change["type"] for change in result.detected_changes}
    assert result.confidence_score == 60


def test_domain_direction():
    assert domain_matches("acme.example", "loans.acme.example")
    assert not domain_matches("loans.acme.example", "acme.example")
    assert not domain_matches("acme.example", "fakeacme.example")


def test_unrelated_source(lender):
    result = compare_lender(
        lender,
        PageData(
            "Other Company",
            "",
            "Buy unrelated household products from Other Company today.",
        ),
        "https://other.example/",
    )
    assert result.status == VerificationStatus.REVIEW_REQUIRED
    assert result.confidence_score == 0
    assert {"NAME_NOT_FOUND", "POSSIBLE_IDENTITY_MISMATCH"} <= {
        change["type"] for change in result.detected_changes
    }


def test_description_explicit_different_identity(lender):
    lender.description = "Other Finance is a provider of business services."
    result = compare_lender(lender, page(), "https://acme.example/")
    assert result.status == VerificationStatus.REVIEW_REQUIRED
    assert result.confidence_score == 75
    assert "DESCRIPTION_REVIEW" in {change["type"] for change in result.detected_changes}


def test_regulator_source_does_not_require_lender_domain(lender):
    lender.source_type = SourceType.REGULATOR
    lender.verification_source_url = "https://regulator.example/records"
    result = compare_lender(lender, page(), lender.verification_source_url)
    assert result.status == VerificationStatus.VERIFIED


def test_thin_page_cannot_verify(lender):
    result = compare_lender(lender, PageData("Acme Finance", "", ""), "https://acme.example/")
    assert result.status == VerificationStatus.REVIEW_REQUIRED


def test_body_only_name_with_domain_is_high_confidence(lender):
    result = compare_lender(
        lender, PageData("Welcome", "", page().visible_text), "https://acme.example/"
    )
    # Strong name + domain evidence can establish basic identity even without metadata.
    assert result.confidence_score == 90
    assert result.status == VerificationStatus.VERIFIED
