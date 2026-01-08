from celery import Celery
from celery.schedules import crontab
from backend.app import create_app

def make_celery():
    app = create_app()

    celery = Celery(
        app.import_name,
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
    )

    # -------------------------------
    # Celery configuration
    # -------------------------------
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,

        beat_schedule={
            "mark-no-shows-every-10-mins": {
                "task": "mark_no_shows_task",
                "schedule": crontab(minute="*/10"),
            },
            "scan-tomorrow-appointments-daily": {
                "task": "scan_tomorrow_appointments_task",
                "schedule": crontab(hour=18, minute=0),  # 6 PM IST
            },
        },
    )

    # Auto-discover tasks from backend/*
    celery.autodiscover_tasks(["backend"])

    # -------------------------------
    # Flask app context for tasks
    # -------------------------------
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()

