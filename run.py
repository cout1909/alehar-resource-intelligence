"""Start the local development API: python run.py."""

import json
import sys
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


def already_running() -> bool:
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open("http://127.0.0.1:8000/health", timeout=2) as response:
            payload = json.load(response)
        return payload.get("service") == "Alehar Resource Intelligence"
    except (URLError, OSError, ValueError):
        return False


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required.")
    if already_running():
        print("The backend is already running. No second server is needed.")
        print("Dashboard (when frontend is running): http://localhost:5173")
        print("API docs: http://127.0.0.1:8000/docs")
        raise SystemExit(0)
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
