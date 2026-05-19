from datetime import datetime, timedelta

from app.models.scheduled_task import ScheduledTask
from app.services.scheduled_tasks import compute_next_run, run_due_scheduled_tasks


def test_compute_next_run_interval():
    task = ScheduledTask(
        enabled=True,
        schedule_type="interval",
        interval_minutes=30,
    )
    now = datetime(2026, 5, 19, 9, 0, 0)

    assert compute_next_run(task, now) == now + timedelta(minutes=30)


def test_compute_next_run_daily_rolls_to_tomorrow():
    task = ScheduledTask(
        enabled=True,
        schedule_type="daily",
        daily_time="08:30",
    )
    now = datetime(2026, 5, 19, 9, 0, 0)

    assert compute_next_run(task, now) == datetime(2026, 5, 20, 8, 30, 0)


def test_compute_next_run_disabled_returns_none():
    task = ScheduledTask(
        enabled=False,
        schedule_type="interval",
        interval_minutes=30,
    )

    assert compute_next_run(task, datetime(2026, 5, 19, 9, 0, 0)) is None


def test_run_due_scheduled_tasks_dispatches(monkeypatch):
    calls: list[int] = []

    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [
                ScheduledTask(
                    id=1,
                    name="due",
                    task_kind="crawl",
                    target_mode="keyword",
                    target_id=1,
                    platform="bilibili",
                    schedule_type="interval",
                    interval_minutes=60,
                    enabled=True,
                    next_run_at=datetime(2026, 5, 19, 8, 0, 0),
                )
            ]

    class FakeSession:
        def query(self, model):
            return FakeQuery()

        def add(self, obj):
            self.obj = obj

        def commit(self):
            pass

    def fake_dispatch(db, task):
        calls.append(task.id)
        return [101]

    monkeypatch.setattr("app.services.scheduled_tasks.dispatch_scheduled_task", fake_dispatch)

    dispatched = run_due_scheduled_tasks(FakeSession(), datetime(2026, 5, 19, 9, 0, 0))

    assert dispatched == 1
    assert calls == [1]
