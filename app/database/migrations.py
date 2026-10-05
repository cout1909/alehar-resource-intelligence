"""Idempotent, additive Phase 2 SQLite migration with a consistent backup."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import Engine, inspect

logger = logging.getLogger(__name__)
COLUMNS = {
    "ai_enabled": "BOOLEAN NOT NULL DEFAULT 0",
    "ai_provider": "VARCHAR(40)",
    "ai_model": "VARCHAR(200)",
    "ai_status": "VARCHAR(40) NOT NULL DEFAULT 'disabled'",
    "ai_analysis": "JSON",
    "ai_extracted_data": "JSON",
    "ai_error": "TEXT",
    "review_status": "VARCHAR(20) NOT NULL DEFAULT 'NOT_REQUIRED'",
    "review_note": "TEXT",
    "reviewed_at": "DATETIME",
}


def migrate_phase_two(engine: Engine) -> Path | None:
    existing = {column["name"] for column in inspect(engine).get_columns("verification_results")}
    missing = {name: ddl for name, ddl in COLUMNS.items() if name not in existing}
    if not missing:
        return None
    if engine.dialect.name != "sqlite":
        raise RuntimeError("This development migration supports SQLite only")
    backup = None
    if engine.url.database and engine.url.database != ":memory:":
        database = Path(engine.url.database).resolve()
        directory = database.parent / ".backups"
        directory.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = directory / f"{database.stem}.pre-phase2.{stamp}.db"
        raw = engine.raw_connection()
        try:
            with sqlite3.connect(backup) as destination:
                raw.driver_connection.backup(destination)
        finally:
            raw.close()
        logger.info("Created pre-migration SQLite backup")
    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            for name, ddl in missing.items():
                # Names and DDL come exclusively from the constants above.
                connection.exec_driver_sql(
                    f"ALTER TABLE verification_results ADD COLUMN {name} {ddl}"
                )
            if "review_status" in missing:
                connection.exec_driver_sql(
                    "UPDATE verification_results SET review_status = 'PENDING' WHERE status != 'VERIFIED'"
                )
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_verification_results_review_status "
                "ON verification_results(review_status)"
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    logger.info("Applied additive Phase 2 migration: %s columns", len(missing))
    return backup
