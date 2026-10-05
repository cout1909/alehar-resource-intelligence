"""Deterministic identity signals, never validation of financial facts."""

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.database.models import Lender, SourceType, VerificationStatus
from app.schemas.verification import ChangeType
from app.services.text_extractor import PageData


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", value).replace("_", " ").split())


def normalize_company_name(value: str) -> str:
    value = normalize_text(value)
    return re.sub(
        r"(?:\s+(?:private limited|pvt ltd|pvt limited|private ltd|limited|ltd|inc|llp))+$",
        "",
        value,
    ).strip()


def name_matches(name: str, text: str) -> bool:
    """Match token-bounded names, allowing punctuation and split brand words."""
    target = normalize_company_name(name).replace(" ", "")
    if not target:
        return False
    words = normalize_text(text).split()
    for index in range(len(words)):
        candidate = ""
        for word in words[index : index + 12]:
            candidate += word
            if candidate == target:
                return True
            if len(candidate) >= len(target):
                break
    return False


def domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        hostname = urlsplit(url).hostname
        return hostname.lower().rstrip(".").removeprefix("www.") if hostname else None
    except ValueError:
        return None


def domain_matches(expected: str | None, actual: str | None) -> bool:
    # Direction matters: bank.example.evil.com is not a bank.example subdomain.
    return bool(expected and actual and (actual == expected or actual.endswith("." + expected)))


@dataclass
class ComparisonResult:
    status: VerificationStatus
    confidence_score: int
    detected_changes: list[dict[str, str]]
    evidence: dict


def compare_lender(lender: Lender, page: PageData, final_url: str) -> ComparisonResult:
    combined = " ".join([page.title, page.meta_description, page.visible_text])
    found = name_matches(lender.name, combined)
    prominent = name_matches(lender.name, page.title + " " + page.meta_description)
    official_website = lender.source_type == SourceType.OFFICIAL_WEBSITE
    expected = domain(lender.website_url if official_website else lender.verification_source_url)
    actual = domain(final_url)
    same_domain = domain_matches(expected, actual)
    changes: list[dict[str, str]] = []

    def flag(kind: ChangeType, message: str) -> None:
        changes.append({"type": kind.value, "message": message})

    if not found:
        flag(
            ChangeType.NAME_NOT_FOUND,
            "The full stored lender name could not be confidently located in the supplied source text. "
            "A shortened brand name may need human confirmation; this is not proof the record is wrong.",
        )
    if expected and not same_domain:
        flag(
            ChangeType.DOMAIN_MISMATCH,
            "Fetched domain differs from the expected source domain; human review recommended.",
        )
    insufficient = len(page.visible_text) < 40
    challenge = any(
        phrase in normalize_text(page.title)
        for phrase in (
            "access denied",
            "just a moment",
            "verify you are human",
            "page not found",
            "captcha",
        )
    )
    if insufficient or challenge:
        flag(
            ChangeType.INSUFFICIENT_CONTENT,
            "Source text is too limited or appears to be a challenge/error page.",
        )
    if not found and (bool(page.title) or (expected and not same_domain)):
        flag(
            ChangeType.POSSIBLE_IDENTITY_MISMATCH,
            "The page identity could not be fully matched to the stored name; human review recommended.",
        )

    # Deliberately narrow: flag only an explicit leading company identity.
    # Missing keywords or financial terms are not proof of a discrepancy.
    identity = re.match(r"^(.{2,100}?)\s+(?:is|are)\s+", lender.description, re.IGNORECASE)
    description_review = bool(
        identity
        and not name_matches(lender.name, identity.group(1))
        and normalize_text(identity.group(1))
        not in {"we", "it", "this company", "the company", "this lender", "the lender"}
    )
    if description_review:
        flag(
            ChangeType.DESCRIPTION_REVIEW,
            "Stored description begins with a different identity; human review recommended.",
        )

    trusted = lender.source_type != SourceType.OTHER_TRUSTED_SOURCE
    score = 20 + (15 if trusted else 10)
    score += 40 if found else -20
    score += 15 if same_domain else (-25 if expected else 0)
    score += 10 if prominent else 0
    score -= 35 if insufficient or challenge else 0
    score -= 25 if description_review else 0
    score = max(0, min(100, score))
    if score < 85 and not changes:
        flag(
            ChangeType.INSUFFICIENT_CONTENT,
            "Identity signals are insufficient for high-confidence verification.",
        )
    status = VerificationStatus.REVIEW_REQUIRED if changes else VerificationStatus.VERIFIED
    if not changes:
        flag(
            ChangeType.NO_CHANGE,
            "Basic source identity appears consistent; financial facts were not evaluated.",
        )
    position = page.visible_text.casefold().find(lender.name.casefold())
    snippet_start = max(0, position - 100) if position >= 0 else 0
    return ComparisonResult(
        status,
        score,
        changes,
        {
            "title": page.title,
            "meta_description": page.meta_description,
            "text_excerpt": page.visible_text[snippet_start : snippet_start + 600],
            "name_found": found,
            "name_in_title_or_meta": prominent,
            "expected_domain": expected,
            "fetched_domain": actual,
            "domain_matches": same_domain,
            "description_check": "explicit_identity_only",
            "scope": "Basic page identity only; no financial facts verified.",
            "score_version": "identity-v1",
        },
    )
