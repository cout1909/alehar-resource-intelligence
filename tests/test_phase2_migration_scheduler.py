import sqlite3
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.db import make_engine
from app.database.migrations import migrate_phase_two
from app.database.models import VerificationResult, VerificationStatus
from app.main import create_app
from app.services import batch
from app.services.scheduler import scheduled_verification


def test_additive_migration_backs_up_preserves_and_is_idempotent(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE verification_results (id INTEGER PRIMARY KEY, status TEXT, evidence JSON)"
        )
        db.executemany(
            "INSERT INTO verification_results VALUES (?, ?, ?)",
            [
                (1, "VERIFIED", '{"old": true}'),
                (2, "SOURCE_UNAVAILABLE", "{}"),
            ],
        )
    engine = make_engine(f"sqlite:///{path.as_posix()}")
    backup = migrate_phase_two(engine)
    assert backup.is_file()
    with sqlite3.connect(backup) as db:
        assert len(db.execute("PRAGMA table_info(verification_results)").fetchall()) == 3
    with sqlite3.connect(path) as db:
        rows = db.execute(
            "SELECT id,status,evidence,review_status FROM verification_results ORDER BY id"
        ).fetchall()
    assert rows == [
        (1, "VERIFIED", '{"old": true}', "NOT_REQUIRED"),
        (2, "SOURCE_UNAVAILABLE", "{}", "PENDING"),
    ]
    assert migrate_phase_two(engine) is None
    assert len(list((tmp_path / ".backups").glob("*.db"))) == 1
    engine.dispose()


def test_scheduler_lock_and_continue_after_lender_failure(client, app, monkeypatch):
    verify = Mock(
        side_effect=[RuntimeError("failure")]
        + [VerificationResult(status=VerificationStatus.VERIFIED) for _ in range(7)]
    )
    monkeypatch.setattr(batch, "verify_lender", verify)
    with app.state.verification_lock:
        scheduled_verification(app)
    verify.assert_not_called()
    scheduled_verification(app)
    assert verify.call_count == 8
    assert not app.state.verification_lock.locked()


def test_scheduler_lifecycle(tmp_path):
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'scheduled.db').as_posix()}",
            scheduler_enabled=True,
        )
    )
    with TestClient(application) as client:
        scheduler = application.state.scheduler
        job = scheduler.get_job("verify-lenders")
        assert job.max_instances == 1 and job.coalesce
        assert client.get("/system/status").json()["scheduler_enabled"] is True
    assert not scheduler.running
