import json
from typing import Any

from app.schemas.ai import SourceIntelligence
from app.services.ai.prompts import EXTRACTION_PROMPT
from app.services.text_extractor import PageData, normalize_whitespace


def extract_source(client: Any, page: PageData, limit: int) -> SourceIntelligence:
    payload = {
        "title": page.title,
        "meta_description": page.meta_description,
        "visible_text": page.visible_text[:limit],
    }
    structured = client.with_structured_output(SourceIntelligence, method="function_calling")
    result = structured.invoke(
        [
            ("system", EXTRACTION_PROMPT),
            ("human", json.dumps(payload, ensure_ascii=False)),
        ],
        config={"callbacks": []},
    )
    extraction = SourceIntelligence.model_validate(result)
    source = normalize_whitespace(" ".join(payload.values())).casefold()
    if any(
        normalize_whitespace(quote).casefold() not in source
        for quote in extraction.identity_evidence
    ):
        raise ValueError("Unsupported evidence quotation")
    return extraction
