"""Curated import: python -m scripts.seed_alehar_demo. Never deletes existing data."""
import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.db import make_engine
from app.database.migrations import migrate_phase_two
from app.database.models import Base, Lender, SourceType, utc_now
from app.database.provenance import backup_sqlite, migrate_provenance

DATASET = Path(__file__).resolve().parents[1] / "data" / "alehar_demo_lenders.json"
logger = logging.getLogger(__name__)


def import_dataset(session, records):
    counts = {"added": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    for record in records:
        matches = session.scalars(select(Lender).where(Lender.name == record["name"])).all()
        if len(matches) > 1:
            raise ValueError("Ambiguous duplicate lender name; resolve before import")
        lender = matches[0] if matches else None
        if lender and not lender.is_demo:
            logger.warning("Skipped non-demo record: %s", record["name"])
            counts["skipped"] += 1
            continue
        values = {key: record[key] for key in (
            "name", "country", "lender_type", "website_url", "alehar_url",
            "verification_source_url", "source_notes")}
        # Legacy schema uses a non-null string; empty means omitted, not a claim.
        values["description"] = record.get("description") or ""
        values["source_type"] = SourceType(record["source_type"])
        values["retrieved_at"] = datetime.fromisoformat(record["retrieved_at"])
        values["is_demo"] = True
        if lender is None:
            session.add(Lender(**values))
            counts["added"] += 1
            logger.info("Added %s", record["name"])
        else:
            def same(key, value):
                old = getattr(lender, key)
                if isinstance(value, datetime) and old:
                    return old.replace(tzinfo=None) == value.replace(tzinfo=None)
                return old == value
            if all(same(key, value) for key, value in values.items()):
                counts["unchanged"] += 1
                continue
            for key, value in values.items():
                setattr(lender, key, value)
            lender.updated_at = utc_now()
            counts["updated"] += 1
            logger.info("Updated curated fields for %s; verification history retained", lender.name)
    session.commit()
    return counts


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = make_engine(get_settings().database_url)
    try:
        Base.metadata.create_all(engine)
        migrate_phase_two(engine)
        migrate_provenance(engine)
        with Session(engine) as session:
            if session.scalar(select(Lender.id).limit(1)) is not None:
                backup_sqlite(engine, "pre-curated-import")
            counts = import_dataset(session, json.loads(DATASET.read_text(encoding="utf-8")))
        logger.info("Import complete: %s", counts)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
