from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Lender, ReviewStatus, VerificationResult


def latest_results(session: Session) -> list[VerificationResult]:
    ids = select(func.max(VerificationResult.id)).group_by(VerificationResult.lender_id)
    return list(
        session.scalars(
            select(VerificationResult)
            .where(VerificationResult.id.in_(ids))
            .order_by(VerificationResult.checked_at.desc(), VerificationResult.id.desc())
        ).all()
    )


def dashboard_summary(session: Session) -> dict:
    latest = latest_results(session)
    review_counts = dict(
        session.execute(
            select(VerificationResult.review_status, func.count()).group_by(
                VerificationResult.review_status
            )
        ).all()
    )
    return {
        "total_lenders": session.scalar(select(func.count()).select_from(Lender)),
        "verified": sum(item.status == "VERIFIED" for item in latest),
        "review_required": sum(item.status == "REVIEW_REQUIRED" for item in latest),
        "source_unavailable": sum(item.status == "SOURCE_UNAVAILABLE" for item in latest),
        "errors": sum(item.status == "ERROR" for item in latest),
        "unverified": session.scalar(select(func.count()).select_from(Lender)) - len(latest),
        "pending_reviews": review_counts.get(ReviewStatus.PENDING, 0),
        "approved_reviews": review_counts.get(ReviewStatus.APPROVED, 0),
        "rejected_reviews": review_counts.get(ReviewStatus.REJECTED, 0),
        "last_verification_time": max((item.checked_at for item in latest), default=None),
    }
