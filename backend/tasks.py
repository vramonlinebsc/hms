from backend.celery_app import celery
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