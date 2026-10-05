import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.batch import verify_batch

logger = logging.getLogger(__name__)


def scheduled_verification(application) -> None:
    state = application.state
    if state.settings.public_demo_mode:
        return
    if not state.verification_lock.acquire(blocking=False):
        logger.info("Scheduled verification skipped: verification already running")
        return
    try:
        with state.session_factory() as session:
            summary = verify_batch(session, state.settings)
        logger.info("Scheduled verification finished: %s", summary.model_dump())
    except Exception:
        logger.error("Scheduled verification failed; next scheduled run remains active")
    finally:
        state.verification_lock.release()


def start_scheduler(application) -> BackgroundScheduler | None:
    if application.state.settings.public_demo_mode or not application.state.settings.scheduler_enabled:
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        scheduled_verification,
        "interval",
        hours=application.state.settings.verification_interval_hours,
        args=[application],
        id="verify-lenders",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("Verification scheduler enabled; first run after configured interval")
    return scheduler
