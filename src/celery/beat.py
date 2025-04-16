from celery.schedules import crontab
from src.celery import celery_app

celery_app.conf.timezone = "Asia/Almaty"     # обязательно!
celery_app.conf.enable_utc = False           # используем локальное время

celery_app.conf.beat_schedule = {
    "run-gog-parser-daily": {
        "task": "src.tasks.parsers.run_gog_parser",
        "schedule": crontab(minute=52, hour=17),  # каждый день в 21:00 (9 вечера)
    },
    "compare-prices-daily": {
        "task": "src.tasks.compare.compare_prices_and_notify",
        "schedule": crontab(minute=0, hour=19),  # каждый день в 19:00
    },
    "enrich-gog-daily": {
        "task": "tasks.enrich_gog_products",  # 👈 без src. если @shared_task без пути
        "schedule": crontab(minute=30, hour=18),
    },
    "enrich-steam-daily": {
        "task": "tasks.enrich_steam_products",
        "schedule": crontab(minute=45, hour=18),
    },
    "update-search-vector-daily": {
    "task": "tasks.update_search_vector",
    "schedule": crontab(minute=15, hour=3),  # каждый день в 03:15 ночи
},

}
