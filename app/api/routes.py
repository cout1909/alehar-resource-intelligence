from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import (
    Lender,
    ReviewStatus,
    VerificationResult,
    VerificationStatus,
)
from app.schemas.lender import LenderListResponse, LenderResponse
from app.schemas.verification import VerificationResponse, VerificationSummary
from app.services.batch import verify_batch
from app.services.verification_service import verify_lender

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
PositiveID = Annotated[int, Path(gt=0)]


@router.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Alehar Resource Intelligence"}


@router.get("/lenders", response_model=LenderListResponse, tags=["Lenders"])
def list_lenders(db: DB) -> dict:
    lenders = db.scalars(select(Lender).order_by(Lender.id)).all()
    return {"total": len(lenders), "lenders": lenders}


@router.get("/lenders/{lender_id}", response_model=LenderResponse, tags=["Lenders"])
def get_lender(lender_id: PositiveID, db: DB) -> Lender:
    lender = db.get(Lender, lender_id)
    if lender is None:
        raise HTTPException(status_code=404, detail="Lender not found")
    return lender


@router.post(
    "/lenders/{lender_id}/verify",
    response_model=VerificationResponse,
    tags=["Verification"],
    description="Manually verify the stored source. No URL input accepted. Business data is never edited.",
)
def verify_one(lender_id: PositiveID, request: Request, db: DB) -> VerificationResult:
    get_lender(lender_id, db)
    if not request.app.state.verification_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Another verification is running; retry after it finishes",
        )
    try:
        return verify_lender(db, lender_id, request.app.state.settings)
    finally:
        request.app.state.verification_lock.release()


@router.post("/verify-all", response_model=VerificationSummary, tags=["Verification"])
def verify_all(request: Request, db: DB) -> VerificationSummary:
    if not request.app.state.verification_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Another verification is running; retry after it finishes",
        )
    try:
        return verify_batch(db, request.app.state.settings)
    finally:
        request.app.state.verification_lock.release()


@router.get("/verification-results", response_model=list[VerificationResponse], tags=["Results"])
def list_results(
    db: DB,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    lender_id: Annotated[int | None, Query(gt=0)] = None,
    status: VerificationStatus | None = None,
    review_status: ReviewStatus | None = None,
) -> list[VerificationResult]:
    query = select(VerificationResult)
    if lender_id is not None:
        query = query.where(VerificationResult.lender_id == lender_id)
    if status is not None:
        query = query.where(VerificationResult.status == status)
    if review_status is not None:
        query = query.where(VerificationResult.review_status == review_status)
    return list(
        db.scalars(
            query.order_by(VerificationResult.checked_at.desc(), VerificationResult.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )


@router.get(
    "/verification-results/{result_id}",
    response_model=VerificationResponse,
    tags=["Results"],
)
def get_result(result_id: PositiveID, db: DB) -> VerificationResult:
    result = db.get(VerificationResult, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Verification result not found")
    return result
