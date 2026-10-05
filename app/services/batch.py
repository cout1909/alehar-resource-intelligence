import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.models import Lender, VerificationStatus
from app.schemas.verification import VerificationSummary
from app.services.verification_service import verify_lender

logger = logging.getLogger(__name__)


def verify_batch(session: Session, settings: Settings) -> VerificationSummary:
    if settings.public_demo_mode:
        raise PermissionError("This action is disabled in the public demo.")
    ids = session.scalars(
        select(Lender.id)
        .where(
            Lender.verification_source_url.is_not(None),
            Lender.verification_source_url != "",
        )
        .order_by(Lender.id)
    ).all()
    summary = VerificationSummary(total=len(ids))
    fields = {
        VerificationStatus.VERIFIED: "verified",
        VerificationStatus.REVIEW_REQUIRED: "review_required",
        VerificationStatus.SOURCE_UNAVAILABLE: "source_unavailable",
        VerificationStatus.ERROR: "errors",
    }
    for index, lender_id in enumerate(ids):
        if index:
            time.sleep(settings.verify_all_delay)
        try:
            result = verify_lender(session, lender_id, settings)
            field = fields[result.status]
            setattr(summary, field, getattr(summary, field) + 1)
        except Exception:
            session.rollback()
            summary.errors += 1
            logger.error("Batch lender failed to persist: lender_id=%s; continuing", lender_id)
    return summary
