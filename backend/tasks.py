from backend.celery_app import celery
from backend.email_utils import send_email


@celery.task(name="send_email_task")
def send_email_task(to_email, subject, body):
    """
    Celery task wrapper for sending emails.
    This task delegates actual email sending
    to the send_email utility.
    """
    send_email(to_email, subject, body)
