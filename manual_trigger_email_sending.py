from backend.tasks import send_email_task

send_email_task.delay(
    "venkateshrr.19@gmail.com",
    "HMS Celery Final Test",
    "Celery email task executed successfully."
)

