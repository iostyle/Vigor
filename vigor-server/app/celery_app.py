from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "vigor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.crawler",
        "app.tasks.processor",
        "app.tasks.updater",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_queues={
        "crawler": {"exchange": "crawler", "routing_key": "crawler"},
        "processor": {"exchange": "processor", "routing_key": "processor"},
        "updater": {"exchange": "updater", "routing_key": "updater"},
    },
    beat_schedule={
        "crawl_all_keywords": {
            "task": "app.tasks.crawler.crawl_all_keywords",
            "schedule": crontab(minute=0),
            "options": {"queue": "crawler"},
        },
        "update_videos": {
            "task": "app.tasks.updater.update_videos",
            "schedule": crontab(minute=0),
            "options": {"queue": "updater"},
        },
    },
)
