import json
import re
from typing import Any

from app.database.models import Lender
from app.schemas.ai import AIAnalysis, SourceIntelligence
from app.services.ai.prompts import ANALYSIS_PROMPT
from app.services.comparator import ComparisonResult


def analyze_source(
    client: Any,
    lender: Lender,
    comparison: ComparisonResult,
    extraction: SourceIntelligence,
) -> AIAnalysis:
    payload = {
        "stored_lender": {
            "name": lender.name,
            "description": lender.description or None,
            "country": lender.country,
            "lender_type": lender.lender_type,
            "is_demo": lender.is_demo,
            "omitted_fields": ["description"] if not lender.description else [],
        },
        "deterministic": {
            "status": comparison.status,
            "changes": comparison.detected_changes,
            "confidence_score": comparison.confidence_score,
            "evidence": comparison.evidence,
        },
        "source_intelligence": extraction.model_dump(),
    }
    structured = client.with_structured_output(AIAnalysis, method="function_calling")
    result = structured.invoke(
        [
            ("system", ANALYSIS_PROMPT),
            ("human", json.dumps(payload, ensure_ascii=False)),
        ],
        config={"callbacks": []},
    )
    analysis = AIAnalysis.model_validate(result)
    # A live output claimed an omitted description "matches". Reject that
    # unsupported comparison instead of showing it as a supported finding.
    if not lender.description and any(
        re.search(r"\bdescription\b.*\b(match\w*|consistent|align\w*|verified)\b", finding, re.I)
        for finding in [analysis.reason or "", *analysis.supported_findings]
    ):
        raise ValueError("Cannot confirm a comparison against an omitted description")
    return analysis
