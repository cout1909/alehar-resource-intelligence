"""One process / one worker. Seed curated public records only on an empty DB."""
import json
import os

import uvicorn
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.db import make_engine
from app.database.migrations import migrate_phase_two
from app.database.models import Base, Lender
from app.database.provenance import migrate_provenance
from app.seed.public_snapshot import restore_public_snapshot
from scripts.seed_alehar_demo import DATASET, import_dataset


def main():
    settings = get_settings()
    engine = make_engine(settings.database_url)
    try:
        Base.metadata.create_all(engine)
        migrate_phase_two(engine)
        migrate_provenance(engine)
        with Session(engine) as session:
            if settings.public_demo_snapshot:
                restore_public_snapshot(session)
            elif session.scalar(select(Lender.id).limit(1)) is None:
                import_dataset(session, json.loads(DATASET.read_text(encoding="utf-8")))
    finally:
        engine.dispose()
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), workers=1)


if __name__ == "__main__":
    main()
