"""Persistence models. Verification never changes lender business fields."""

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(StrEnum):
    OFFICIAL_WEBSITE = "OFFICIAL_WEBSITE"
    REGULATOR = "REGULATOR"
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    OTHER_TRUSTED_SOURCE = "OTHER_TRUSTED_SOURCE"


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    ERROR = "ERROR"


class ReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"


class Base(DeclarativeBase):
    pass


class Lender(Base):
    __tablename__ = "lenders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(100))
    lender_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    alehar_url: Mapped[str | None] = mapped_column(String(2048))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_notes: Mapped[str | None] = mapped_column(Text)
    verification_source_url: Mapped[str | None] = mapped_column(String(2048))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    lender_id: Mapped[int] = mapped_column(ForeignKey("lenders.id"), index=True)
    status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_http_status: Mapped[int | None] = mapped_column(Integer)
    source_reachable: Mapped[bool] = mapped_column(Boolean)
    detected_changes: Mapped[list[dict]] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON)
    confidence_score: Mapped[int] = mapped_column(Integer)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_provider: Mapped[str | None] = mapped_column(String(40))
    ai_model: Mapped[str | None] = mapped_column(String(200))
    ai_status: Mapped[str] = mapped_column(String(40), default="disabled")
    ai_analysis: Mapped[dict | None] = mapped_column(JSON)
    ai_extracted_data: Mapped[dict | None] = mapped_column(JSON)
    ai_error: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.NOT_REQUIRED, index=True
    )
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
