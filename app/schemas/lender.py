from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.database.models import SourceType


class LenderCreate(BaseModel):
    """Import schema for future curated imports; no write API in Phase 1."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=100)
    lender_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=10000)
    website_url: HttpUrl | None = None
    alehar_url: HttpUrl | None = None
    verification_source_url: HttpUrl | None = None
    source_type: SourceType = SourceType.OFFICIAL_WEBSITE
    active: bool = True
    is_demo: bool = False


class LenderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    country: str
    lender_type: str
    description: str
    website_url: str | None
    alehar_url: str | None
    retrieved_at: datetime | None = None
    source_notes: str | None = None
    verification_source_url: str | None
    source_type: SourceType
    active: bool
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    last_verified_at: datetime | None

    @field_validator("created_at", "updated_at", "last_verified_at", "retrieved_at")
    @classmethod
    def attach_utc(cls, value: datetime | None) -> datetime | None:
        # SQLite returns naive timestamps; this app stores UTC exclusively.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class LenderListResponse(BaseModel):
    total: int
    lenders: list[LenderResponse]
