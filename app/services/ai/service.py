import logging
from dataclasses import dataclass

from app.core.config import Settings
from app.database.models import Lender
from app.schemas.ai import AIAnalysis, SourceIntelligence
from app.services.ai.analyzer import analyze_source
from app.services.ai.client import create_client
from app.services.ai.extractor import extract_source
from app.services.comparator import ComparisonResult
from app.services.text_extractor import PageData

logger = logging.getLogger(__name__)


@dataclass
class AIOutcome:
    status: str
    extraction: SourceIntelligence | None = None
    analysis: AIAnalysis | None = None
    error: str | None = None


def enrich_verification(
    settings: Settings,
    lender: Lender,
    page: PageData,
    comparison: ComparisonResult,
) -> AIOutcome:
    if not settings.ai_active:
        return AIOutcome(settings.ai_config_status)
    try:
        from langsmith import tracing_context

        # Explicitly prevent ambient tracing settings from forwarding source
        # records to a separate service. Only Groq receives the requested data.
        with tracing_context(enabled=False):
            client = create_client(settings)
            extraction = extract_source(client, page, settings.ai_max_input_chars)
            analysis = analyze_source(client, lender, comparison, extraction)
        # Never persist a credential even if a provider echoes one unexpectedly.
        secret = settings.groq_api_key.get_secret_value()
        if secret and secret in (extraction.model_dump_json() + analysis.model_dump_json()):
            raise ValueError("Provider output contained a protected value")
        return AIOutcome("success", extraction, analysis)
    except Exception as error:
        # Raw provider errors may contain authorization headers or supplied data.
        # Do not log exception strings, tracebacks, prompts, or provider bodies.
        status = getattr(error, "status_code", None)
        if status == 429:
            reason = "Groq rate limit reached. Try a later verification."
        elif status in (401, 403):
            reason = "Groq authentication or model permission was declined. Check backend AI configuration."
        elif status == 404:
            reason = "The configured Groq model is unavailable to this account."
        elif isinstance(error, (TimeoutError,)) or "Timeout" in type(error).__name__:
            reason = "Groq did not respond within the configured time limit."
        elif isinstance(error, ValueError):
            reason = "AI output could not be validated against the required structure or source evidence."
        else:
            reason = "AI service unavailable for this check."
        logger.warning("Groq enhancement unavailable; retained deterministic verification")
        return AIOutcome(
            "unavailable",
            error=f"{reason} Deterministic verification was retained.",
        )
