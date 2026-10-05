from typing import Any

from app.core.config import Settings


def create_client(settings: Settings) -> Any:
    """Lazy import keeps disabled AI independent of provider initialization."""
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.ai_model.strip(),
        temperature=settings.ai_temperature,
        groq_api_key=settings.groq_api_key,
        timeout=settings.ai_timeout,
        max_retries=0,
        max_tokens=1800,
    )
