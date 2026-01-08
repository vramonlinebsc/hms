from backend.celery_app import celery
from backend.db import get_db
from datetime import date,timedelta
from backend.email_utils import send_email
import logging

logger = logging.getLogger(__name__)

@celery.task(
    name="send_email_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_email_task(to_email, subject, body):
    send_email(to_email, subject, body)

@celery.task(name="mark_no_shows_task")
def mark_no_shows_task():
    """
    Periodic task triggered by Celery Beat.

    CURRENT BEHAVIOR (INTENTIONAL):
    - No DB access
    - No updates
    - No emails
    - No side effects

    PURPOSE:
    - Validate Beat → Worker → Task execution pipeline
    - Provide stable anchor for future NO_SHOW automation
    """
    logger.info("mark_no_shows_task executed (skeleton only)")

@celery.task(name="scan_tomorrow_appointments_task")
def scan_tomorrow_appointments_task():
    """
    READ-ONLY domain task.

    - Scans appointments scheduled for tomorrow
    - Logs count and appointment IDs
    - NO updates
    - NO emails
    - NO scheduling assumptions
    """

    db = get_db()

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    rows = db.execute(
        """
        SELECT id
        FROM appointments
        WHERE date = ?
          AND status = 'BOOKED'
        ORDER BY id
        """,
        (tomorrow,)
    ).fetchall()

    appointment_ids = [row["id"] for row in rows]

    logger.info(
        "scan_tomorrow_appointments_task | date=%s | count=%d | ids=%s",
        tomorrow,
        len(appointment_ids),
        appointment_ids
    )

    return {
        "date": tomorrow,
        "count": len(appointment_ids),
        "appointment_ids": appointment_ids,
    }
