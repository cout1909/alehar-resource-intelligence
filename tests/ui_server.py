"""Browser-test server only: isolated temporary DB and synthetic HTTP responses.

Never import this module from the application. No provider or live scraping.
"""

import os
import tempfile
from pathlib import Path

import uvicorn

from app.core.config import Settings
from app.main import create_app
from app.seed.lenders import SEED_LENDERS
from app.services import verification_service
from app.services.source_fetcher import FetchResult


def fake_source(url, settings):
    name = next(name for name, source in SEED_LENDERS if source == url)
    if name == "ICICI Bank":
        return FetchResult(url, url, error="Synthetic test: source unavailable")
    if name == "SIDBI":
        return FetchResult(
            url,
            url,
            200,
            True,
            "text/html",
            "<title>Unrelated test page</title><p>This synthetic source has no matching identity.</p>",
        )
    return FetchResult(
        url,
        url,
        200,
        True,
        "text/html",
        f"<title>{name}</title><p>{name}: synthetic public source information for an isolated browser workflow test.</p>",
    )


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="alehar-ui-") as directory:
        verification_service.fetch_source = fake_source
        app = create_app(
            Settings(
                database_url=f"sqlite:///{(Path(directory) / 'ui.db').as_posix()}",
                frontend_origin="http://localhost:5174",
                verify_all_delay=0,
                ai_enabled=False,
                scheduler_enabled=False,
            )
        )
        if os.environ.get("UI_TEST_PUBLIC_MODE") == "1":
            app.state.settings.public_demo_mode = True
            app.state.settings.public_demo_snapshot = True
            app.state.settings.scheduler_enabled = True
        uvicorn.run(app, host="127.0.0.1", port=8001)
