"""Additive provenance migration; existing business data and results are retained."""
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect


def backup_sqlite(engine, reason="phase3"):
    if engine.dialect.name != "sqlite" or engine.url.database in {None, "", ":memory:"}:
        return None
    database = Path(engine.url.database).resolve()
    directory = database.parent / ".backups"
    directory.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = directory / f"{database.stem}.{reason}.{stamp}.db"
    raw = engine.raw_connection()
    try:
        with sqlite3.connect(destination) as target:
            raw.driver_connection.backup(target)
    finally:
        raw.close()
    logging.getLogger(__name__).info("Created consistent SQLite backup (%s)", reason)
    return destination


def migrate_provenance(engine):
    columns = {column["name"] for column in inspect(engine).get_columns("lenders")}
    missing = {name: ddl for name, ddl in {"retrieved_at": "TIMESTAMP", "source_notes": "TEXT"}.items()
               if name not in columns}
    if not missing:
        return
    backup_sqlite(engine)
    with engine.begin() as connection:
        for name, ddl in missing.items():
            connection.exec_driver_sql(f"ALTER TABLE lenders ADD COLUMN {name} {ddl}")
