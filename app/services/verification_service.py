import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.models import (
    Lender,
    ReviewStatus,
    VerificationResult,
    VerificationStatus,
    utc_now,
)
from app.schemas.verification import ChangeType
from app.services.ai.service import enrich_verification
from app.services.comparator import compare_lender
from app.services.source_fetcher import FetchResult, fetch_source
from app.services.text_extractor import extract_metadata

logger = logging.getLogger(__name__)
Fetcher = Callable[[str], FetchResult]


def verify_lender(
    session: Session,
    lender_id: int,
    settings: Settings,
    fetcher: Fetcher | None = None,
) -> VerificationResult:
    if settings.public_demo_mode:
        raise PermissionError("This action is disabled in the public demo.")
    lender = session.get(Lender, lender_id)
    if lender is None:
        raise LookupError("Lender not found")
    logger.info("Verification started: lender_id=%s", lender_id)
    result = VerificationResult(
        lender_id=lender.id,
        source_url=lender.verification_source_url,
        source_reachable=False,
        confidence_score=0,
        detected_changes=[],
        evidence={},
        checked_at=utc_now(),
        ai_enabled=settings.ai_active,
        ai_provider=settings.ai_provider if settings.ai_active else None,
        ai_model=settings.ai_model if settings.ai_active else None,
        ai_status="skipped" if settings.ai_active else settings.ai_config_status,
    )
    try:
        if not lender.verification_source_url:
            fetched = FetchResult(
                "",
                "",
                error="No verification source configured",
                error_kind="missing_source",
            )
        else:
            fetched = (
                fetcher(lender.verification_source_url)
                if fetcher
                else fetch_source(lender.verification_source_url, settings)
            )
        result.source_http_status = fetched.status_code
        result.source_reachable = fetched.reachable
        result.error_message = fetched.error
        result.evidence = {
            "final_url": fetched.final_url or None,
            "content_type": fetched.content_type,
            "fetch_error_kind": fetched.error_kind,
        }
        if not fetched.reachable:
            result.status = VerificationStatus.SOURCE_UNAVAILABLE
            result.detected_changes = [
                {
                    "type": ChangeType.SOURCE_UNREACHABLE.value,
                    "message": "Could not independently verify: "
                    + (fetched.error or "source unavailable"),
                }
            ]
        elif fetched.error:
            result.status = VerificationStatus.REVIEW_REQUIRED
            result.detected_changes = [
                {
                    "type": ChangeType.UNSUPPORTED_CONTENT.value,
                    "message": fetched.error + "; human review recommended.",
                }
            ]
        else:
            page = extract_metadata(fetched.html, settings.max_source_text_length)
            comparison = compare_lender(lender, page, fetched.final_url)
            result.status = comparison.status
            result.confidence_score = comparison.confidence_score
            result.detected_changes = comparison.detected_changes
            result.evidence = {**result.evidence, **comparison.evidence}
            result.evidence["deterministic_status"] = comparison.status.value
            outcome = enrich_verification(settings, lender, page, comparison)
            result.ai_status = outcome.status
            result.ai_error = outcome.error
            if outcome.analysis is not None and outcome.extraction is not None:
                result.ai_analysis = outcome.analysis.model_dump()
                result.ai_extracted_data = outcome.extraction.model_dump()
                analysis = outcome.analysis
                if (
                    analysis.review_recommended
                    or analysis.possible_mismatch
                    or analysis.identity_match is not True
                    or analysis.uncertain_findings
                ):
                    result.status = VerificationStatus.REVIEW_REQUIRED
                    result.detected_changes = [
                        item
                        for item in result.detected_changes
                        if item["type"] != ChangeType.NO_CHANGE.value
                    ] + [
                        {
                            "type": ChangeType.AI_REVIEW.value,
                            "message": "AI-assisted analysis recommends human review; findings may be inaccurate.",
                        }
                    ]
    except Exception:
        # Unexpected processing failures become recorded ERROR outcomes. Database
        # errors below deliberately propagate so the API cannot claim persistence.
        logger.exception("Unexpected verification error: lender_id=%s", lender_id)
        result.status = VerificationStatus.ERROR
        result.confidence_score = 0
        result.error_message = "Internal verification error; inspect the application log."
        result.detected_changes = [
            {
                "type": ChangeType.INTERNAL_ERROR.value,
                "message": "Could not independently verify; internal processing failed.",
            }
        ]
    result.review_status = (
        ReviewStatus.NOT_REQUIRED
        if result.status == VerificationStatus.VERIFIED
        else ReviewStatus.PENDING
    )
    lender.last_verified_at = result.checked_at
    session.add(result)
    session.commit()
    session.refresh(result)
    logger.info("Verification finished: lender_id=%s status=%s", lender_id, result.status)
    return result
