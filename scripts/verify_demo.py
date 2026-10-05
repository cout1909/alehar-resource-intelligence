"""Explicit operator action: verify only curated lenders and report actual outcomes."""
import json
import time
from collections import Counter
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.db import make_engine
from app.database.models import Lender, utc_now
from app.services.verification_service import verify_lender
from scripts.seed_alehar_demo import DATASET


def main():
    settings = get_settings()
    if settings.public_demo_mode:
        raise SystemExit("Verification is disabled in public demo mode.")
    names = {row["name"] for row in json.loads(DATASET.read_text(encoding="utf-8"))}
    engine = make_engine(settings.database_url)
    rows = []
    try:
        with Session(engine) as session:
            lenders = session.scalars(select(Lender).where(Lender.name.in_(names), Lender.alehar_url.is_not(None)).order_by(Lender.id)).all()
            if len(lenders) != len(names):
                raise SystemExit("Import the complete curated dataset before verification.")
            for lender in lenders:
                result = verify_lender(session, lender.id, settings)
                row = {"name": lender.name, "lender_id": lender.id, "result_id": result.id,
                       "status": result.status.value, "ai_status": result.ai_status,
                       "score": result.confidence_score, "checked_at": result.checked_at.replace(tzinfo=utc_now().tzinfo).isoformat(),
                       "signals": [item["type"] for item in result.detected_changes],
                       "ai_error": result.ai_error}
                rows.append(row)
                print(f"{lender.name}: {result.status.value}; AI {result.ai_status}", flush=True)
                time.sleep(settings.verify_all_delay)
    finally:
        engine.dispose()
    report = {"generated_at": utc_now().isoformat(), "records_monitored": len(rows),
              "counts": dict(Counter(row["status"] for row in rows)),
              "ai_status_counts": dict(Counter(row["ai_status"] for row in rows)),
              "ai_fallbacks": sum(row["ai_status"] in {"unavailable", "not_configured"} for row in rows),
              "verify_all_delay_seconds": settings.verify_all_delay,
              "ai_max_input_chars": settings.ai_max_input_chars,
              "ai_model": settings.ai_model if settings.ai_active else None, "records": rows}
    Path("docs/verification-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Report written to docs/verification-report.json", flush=True)


if __name__ == "__main__":
    main()
