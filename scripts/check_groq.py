"""Optional live diagnostic. Prints only stages and safe error categories.

Run from the repository root: python -m scripts.check_groq
Never prints credentials, supplied source text, or raw provider exceptions.
"""

from app.core.config import get_settings
from app.services.ai.client import create_client
from app.services.ai.extractor import extract_source
from app.services.text_extractor import PageData


def main() -> None:
    settings = get_settings()
    if not settings.ai_active:
        print(f"AI configuration: {settings.ai_config_status}")
        return
    stage = "client initialization"
    try:
        client = create_client(settings)
        stage = "structured extraction"
        result = extract_source(
            client,
            PageData(
                "Diagnostic Company",
                "Synthetic diagnostic page, not a real financial entity.",
                "Diagnostic Company. This is a synthetic connectivity check. No products or financial facts are supplied.",
            ),
            settings.ai_max_input_chars,
        )
        print(f"Groq structured extraction succeeded: {type(result).__name__}")
    except Exception as error:
        print(f"Failed stage: {stage}")
        print(f"Error class: {type(error).__name__}")
        status = getattr(error, "status_code", None)
        if isinstance(status, int):
            print(f"Provider HTTP status: {status}")
        if type(error).__name__ == "ValidationError":
            print("Structured output did not match the required schema.")


if __name__ == "__main__":
    main()
