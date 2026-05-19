from celery import Celery

from app.celery_app import celery_app


def test_celery_app_instance():
    assert isinstance(celery_app, Celery)
    assert celery_app.main == "vigor"


def test_celery_broker_and_backend_configured():
    assert celery_app.conf.broker_url
    assert celery_app.conf.result_backend


def test_celery_queues_configured():
    queues = celery_app.conf.task_queues
    assert "crawler" in queues
    assert "processor" in queues
    assert "updater" in queues


def test_celery_basic_config():
    assert celery_app.conf.task_serializer == "json"
    assert "json" in celery_app.conf.accept_content
    assert celery_app.conf.timezone == "Asia/Shanghai"
    assert celery_app.conf.task_track_started is True


def test_celery_beat_schedule():
    schedule = celery_app.conf.beat_schedule
    assert "run_scheduled_tasks" in schedule
    assert schedule["run_scheduled_tasks"]["options"]["queue"] == "updater"
    assert "crawl_all_keywords" not in schedule
    assert "update_videos" not in schedule
