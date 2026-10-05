"""Restore a reviewed, public-only snapshot. Never fetch sources or call AI."""
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.database.models import (
    Lender,
    ReviewStatus,
    SourceType,
    VerificationResult,
    VerificationStatus,
)
from app.schemas.verification import VerificationResponse

DATA = Path(__file__).resolve().parents[2] / "data"


def restore_public_snapshot(session):
    records = json.loads((DATA / "alehar_demo_lenders.json").read_text(encoding="utf-8"))
    snapshot = json.loads((DATA / "public_demo_results.json").read_text(encoding="utf-8"))
    if snapshot["schema_version"] != 1:
        raise ValueError("Unsupported public snapshot version")
    results = [VerificationResponse.model_validate(row) for row in snapshot["results"]]
    if (len(records) != len(results) or len({row.id for row in results}) != len(results)
            or {row.lender_id for row in results} != set(range(1, len(records) + 1))):
        raise ValueError("Public snapshot records and results must match exactly")
    lender_count = session.scalar(select(func.count()).select_from(Lender))
    result_count = session.scalar(select(func.count()).select_from(VerificationResult))
    if lender_count or result_count:
        # Never replace an existing/local database or erase user decisions.
        existing = [session.get(Lender, index) for index in range(1, len(records) + 1)]
        saved = [session.get(VerificationResult, row.id) for row in results]
        if (lender_count != len(records) or result_count != len(results)
                or any(not row or row.name != record["name"] for row, record in zip(existing, records))
                or any(not row or VerificationResponse.model_validate(row).model_dump(mode="json") != expected.model_dump(mode="json")
                       for row, expected in zip(saved, results))):
            raise ValueError("Public snapshot needs an empty disposable database; existing data was preserved")
        return False
    by_lender = {row.lender_id: row for row in results}
    try:
        for index, record in enumerate(records, 1):
            result = by_lender[index]
            if result.source_url != record["verification_source_url"]:
                raise ValueError("Snapshot source does not match curated provenance")
            if result.review_note or result.reviewed_at:
                raise ValueError("Public snapshot must not include private review notes")
            values = {key: record[key] for key in ("name", "country", "lender_type", "website_url",
                      "alehar_url", "verification_source_url", "source_notes")}
            session.add(Lender(id=index, **values, description=record.get("description") or "",
                               source_type=SourceType(record["source_type"]), is_demo=True,
                               retrieved_at=datetime.fromisoformat(record["retrieved_at"]),
                               last_verified_at=result.checked_at))
        session.flush()
        for result in results:
            values = result.model_dump()
            values["status"] = VerificationStatus(values["status"])
            values["review_status"] = ReviewStatus(values["review_status"])
            session.add(VerificationResult(**values))
        session.commit()
    except Exception:
        session.rollback()
        raise
    return True
