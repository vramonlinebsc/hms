from celery import Celery
from backend.app import create_app

def make_celery():
    app = create_app()

    celery = Celery(
        app.import_name,
        broker="redis://localhost:6380/0",
        backend="redis://localhost:6380/0",
    )
    from celery.schedules import crontab

    celery.conf.beat_schedule = {
       "mark-no-shows-every-10-mins": {
            "task": "mark_no_shows_task",
            "schedule": crontab(minute="*/10"),
      }
   }

    celery.autodiscover_tasks(["backend"])


    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery



celery = make_celery()
