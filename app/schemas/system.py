from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class DashboardSummary(BaseModel):
    total_lenders: int
    verified: int
    review_required: int
    source_unavailable: int
    errors: int
    unverified: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
    last_verification_time: datetime | None

    @field_validator("last_verification_time")
    @classmethod
    def utc(cls, value: datetime | None) -> datetime | None:
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


class SystemStatus(BaseModel):
    public_demo_mode: bool = False
    public_demo_snapshot: bool = False
    backend_status: str
    database_status: str
    ai_enabled: bool
    ai_provider: str
    ai_model: str | None
    ai_status: str
    ai_message: str
    scheduler_enabled: bool
    verification_interval_hours: float
    next_scheduled_run: datetime | None
    verification_running: bool
