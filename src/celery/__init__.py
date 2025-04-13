from celery import Celery

celery_app = Celery(
    "project",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

celery_app.autodiscover_tasks(["src.tasks.parsers"])


celery_app.conf.timezone = "Asia/Almaty"
celery_app.conf.enable_utc = False
