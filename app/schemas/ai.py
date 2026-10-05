"""Bounded structured provider outputs; schema errors trigger fallback."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

ShortText = Annotated[str, Field(max_length=1200)]
Items = Annotated[list[ShortText], Field(max_length=15)]


class SourceIntelligence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    company_name: ShortText | None
    company_description: ShortText | None
    entity_type: ShortText | None
    products_or_services: Items
    geographies: Items
    identity_evidence: Items
    uncertain_fields: Items
    source_summary: ShortText | None


class AIAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    identity_match: bool | None
    possible_mismatch: bool
    review_recommended: bool
    reason: ShortText | None
    supported_findings: Items
    uncertain_findings: Items
