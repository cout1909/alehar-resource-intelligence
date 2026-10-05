from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy import select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Lender, ReviewStatus, VerificationResult, utc_now
from app.schemas.system import DashboardSummary, SystemStatus
from app.schemas.verification import (
    ReviewQueueItem,
    ReviewRequest,
    VerificationResponse,
)
from app.services.reporting import dashboard_summary, latest_results

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
ID = Annotated[int, Path(gt=0)]


def decide(session: Session, result_id: int, body: ReviewRequest, status: ReviewStatus):
    if session.get(VerificationResult, result_id) is None:
        raise HTTPException(404, "Verification result not found")
    changed = session.execute(
        update(VerificationResult)
        .where(
            VerificationResult.id == result_id,
            VerificationResult.review_status == ReviewStatus.PENDING,
        )
        .values(review_status=status, review_note=body.note or None, reviewed_at=utc_now())
    )
    if changed.rowcount != 1:
        session.rollback()
        raise HTTPException(
            409, "This result is no longer pending review. Refresh to see its decision."
        )
    session.commit()
    session.expire_all()
    return session.get(VerificationResult, result_id)


@router.post(
    "/verification-results/{result_id}/approve",
    response_model=VerificationResponse,
    tags=["Human review"],
)
def approve(result_id: ID, body: ReviewRequest, db: DB):
    return decide(db, result_id, body, ReviewStatus.APPROVED)


@router.post(
    "/verification-results/{result_id}/reject",
    response_model=VerificationResponse,
    tags=["Human review"],
)
def reject(result_id: ID, body: ReviewRequest, db: DB):
    return decide(db, result_id, body, ReviewStatus.REJECTED)


@router.get("/reviews/pending", response_model=list[ReviewQueueItem], tags=["Human review"])
def pending(
    db: DB,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    rows = db.execute(
        select(VerificationResult, Lender.name)
        .join(Lender)
        .where(VerificationResult.review_status == ReviewStatus.PENDING)
        .order_by(VerificationResult.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        {
            **VerificationResponse.model_validate(result).model_dump(),
            "lender_name": name,
        }
        for result, name in rows
    ]


@router.get(
    "/lenders/{lender_id}/history",
    response_model=list[VerificationResponse],
    tags=["History"],
)
def lender_history(
    lender_id: ID,
    db: DB,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if db.get(Lender, lender_id) is None:
        raise HTTPException(404, "Lender not found")
    return db.scalars(
        select(VerificationResult)
        .where(VerificationResult.lender_id == lender_id)
        .order_by(VerificationResult.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()


@router.get("/dashboard/summary", response_model=DashboardSummary, tags=["Dashboard"])
def summary(db: DB):
    return dashboard_summary(db)


@router.get("/dashboard/latest", response_model=list[VerificationResponse], tags=["Dashboard"])
def latest(db: DB):
    return latest_results(db)


@router.get("/system/status", response_model=SystemStatus, tags=["System"])
def system_status(request: Request, db: DB):
    settings = request.app.state.settings
    database_status = "connected"
    latest_ai = None
    try:
        db.execute(text("SELECT 1"))
        if settings.ai_active:
            latest_ai = db.scalar(
                select(VerificationResult.ai_status)
                .where(
                    VerificationResult.ai_model == settings.ai_model,
                    VerificationResult.ai_status.in_(["success", "unavailable"]),
                )
                .order_by(VerificationResult.id.desc())
                .limit(1)
            )
    except SQLAlchemyError:
        db.rollback()
        database_status = "error"
    ai_status = latest_ai or settings.ai_config_status
    messages = {
        "disabled": "AI analysis is not enabled. Deterministic verification is still active.",
        "not_configured": "AI requires a backend API key and model. Deterministic verification is still active.",
        "ready": "AI is configured; provider connectivity will be checked on the next verification.",
        "success": "The most recent AI operation succeeded. Availability may change.",
        "unavailable": "AI is unavailable. Deterministic verification is still active; next verification retries AI.",
    }
    scheduler = request.app.state.scheduler
    job = scheduler.get_job("verify-lenders") if scheduler else None
    return {
        "backend_status": "online",
        "public_demo_mode": settings.public_demo_mode,
        "public_demo_snapshot": settings.public_demo_snapshot,
        "database_status": database_status,
        "ai_enabled": settings.ai_active,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model or None,
        "ai_status": ai_status,
        "ai_message": messages[ai_status],
        "scheduler_enabled": bool(scheduler and scheduler.running),
        "verification_interval_hours": settings.verification_interval_hours,
        "next_scheduled_run": job.next_run_time if job else None,
        "verification_running": request.app.state.verification_lock.locked(),
    }
