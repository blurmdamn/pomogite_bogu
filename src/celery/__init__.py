from celery import Celery
from src.config import celery_settings  # импорт настроек из .env

celery_app = Celery(
    "project",
    broker=celery_settings.REDIS_URL,
    backend=celery_settings.REDIS_URL,
)

celery_app.autodiscover_tasks([
    "src.tasks.parsers",
    "src.tasks.compare",
    "src.tasks.enrichment",
    "src.tasks.vector",
])

celery_app.conf.timezone = "Asia/Almaty"
celery_app.conf.enable_utc = False
