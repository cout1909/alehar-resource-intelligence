from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database.models import ReviewStatus, VerificationStatus


class ChangeType(StrEnum):
    NAME_NOT_FOUND = "NAME_NOT_FOUND"
    POSSIBLE_IDENTITY_MISMATCH = "POSSIBLE_IDENTITY_MISMATCH"
    DOMAIN_MISMATCH = "DOMAIN_MISMATCH"
    DESCRIPTION_REVIEW = "DESCRIPTION_REVIEW"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    INSUFFICIENT_CONTENT = "INSUFFICIENT_CONTENT"
    UNSUPPORTED_CONTENT = "UNSUPPORTED_CONTENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NO_CHANGE = "NO_CHANGE"
    AI_REVIEW = "AI_REVIEW"


class DetectedChange(BaseModel):
    type: ChangeType
    message: str


class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lender_id: int
    status: VerificationStatus
    source_url: str | None
    source_http_status: int | None
    source_reachable: bool
    detected_changes: list[DetectedChange]
    evidence: dict[str, Any]
    confidence_score: int = Field(ge=0, le=100)
    checked_at: datetime
    error_message: str | None
    ai_enabled: bool = False
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_status: str = "disabled"
    ai_analysis: dict[str, Any] | None = None
    ai_extracted_data: dict[str, Any] | None = None
    ai_error: str | None = None
    review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED
    review_note: str | None = None
    reviewed_at: datetime | None = None

    @field_validator("reviewed_at")
    @classmethod
    def review_utc(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value

    @field_validator("checked_at")
    @classmethod
    def attach_utc(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class VerificationSummary(BaseModel):
    total: int = 0
    verified: int = 0
    review_required: int = 0
    source_unavailable: int = 0
    errors: int = 0


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    note: str | None = Field(default=None, max_length=2000)


class ReviewQueueItem(VerificationResponse):
    lender_name: str
