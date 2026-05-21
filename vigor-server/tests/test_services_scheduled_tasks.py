from datetime import datetime, timedelta

from app.models.scheduled_task import ScheduledTask
from app.models.scheduled_task_run import ScheduledTaskRun
from app.services.scheduled_tasks import (
    compute_next_run,
    dispatch_scheduled_task,
    run_due_scheduled_tasks,
)


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
        def __init__(self):
            self.runs = []

        def query(self, model):
            return FakeQuery()

        def add(self, obj):
            self.obj = obj
            if isinstance(obj, ScheduledTaskRun) and obj not in self.runs:
                self.runs.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            obj.id = obj.id or 1

    def fake_dispatch(db, task, source="scheduled", source_id=None):
        calls.append(task.id)
        return [101]

    monkeypatch.setattr("app.services.scheduled_tasks.dispatch_scheduled_task", fake_dispatch)

    dispatched = run_due_scheduled_tasks(FakeSession(), datetime(2026, 5, 19, 9, 0, 0))

    assert dispatched == 1
    assert calls == [1]


def test_run_due_scheduled_tasks_passes_source_to_dispatcher(monkeypatch):
    captured: dict[str, int] = {}

    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [
                ScheduledTask(
                    id=7,
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
        def __init__(self):
            self.runs = []

        def query(self, model):
            return FakeQuery()

        def add(self, obj):
            self.obj = obj
            if isinstance(obj, ScheduledTaskRun) and obj not in self.runs:
                self.runs.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            obj.id = obj.id or 1

    def fake_dispatch(db, task, source, source_id):
        captured["source"] = source
        captured["source_id"] = source_id
        return [101]

    monkeypatch.setattr("app.services.scheduled_tasks.dispatch_scheduled_task", fake_dispatch)

    run_due_scheduled_tasks(FakeSession(), datetime(2026, 5, 19, 9, 0, 0))

    assert captured == {"source": "scheduled", "source_id": 7}


def test_run_due_scheduled_tasks_records_run(monkeypatch):
    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [
                ScheduledTask(
                    id=9,
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
        def __init__(self):
            self.runs: list[ScheduledTaskRun] = []

        def query(self, model):
            return FakeQuery()

        def add(self, obj):
            if isinstance(obj, ScheduledTaskRun) and obj not in self.runs:
                self.runs.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            obj.id = obj.id or 1

    monkeypatch.setattr(
        "app.services.scheduled_tasks.dispatch_scheduled_task",
        lambda db, task, source="scheduled", source_id=None: [501, 502],
    )
    session = FakeSession()

    dispatched = run_due_scheduled_tasks(session, datetime(2026, 5, 19, 9, 0, 0))

    assert dispatched == 1
    assert len(session.runs) == 1
    assert session.runs[0].status == "success"
    assert session.runs[0].due_count == 1
    assert session.runs[0].dispatched_count == 1
    assert session.runs[0].failed_count == 0
    assert session.runs[0].triggered_task_ids == "[501, 502]"


def test_run_due_scheduled_tasks_records_error_summary(monkeypatch):
    class FakeQuery:
        def filter(self, *args):
            return self

        def all(self):
            return [
                ScheduledTask(
                    id=11,
                    name="broken",
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
        def __init__(self):
            self.runs: list[ScheduledTaskRun] = []

        def query(self, model):
            return FakeQuery()

        def add(self, obj):
            if isinstance(obj, ScheduledTaskRun) and obj not in self.runs:
                self.runs.append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            obj.id = obj.id or 1

    def fake_dispatch(db, task, source="scheduled", source_id=None):
        raise RuntimeError("keyword disabled")

    monkeypatch.setattr("app.services.scheduled_tasks.dispatch_scheduled_task", fake_dispatch)
    session = FakeSession()

    dispatched = run_due_scheduled_tasks(session, datetime(2026, 5, 19, 9, 0, 0))

    assert dispatched == 0
    assert session.runs[0].status == "failed"
    assert session.runs[0].failed_count == 1
    assert session.runs[0].error_message == "定时任务 11: keyword disabled"


def test_dispatch_scheduled_update_category_passes_platform(monkeypatch):
    captured: dict[str, object] = {}
    task = ScheduledTask(
        id=12,
        name="update category",
        task_kind="update",
        target_mode="category",
        target_id=3,
        platform="bilibili",
        limit=10,
        schedule_type="daily",
        daily_time="01:00",
        enabled=True,
    )

    def fake_dispatch_update_category(db, category_id, limit, **kwargs):
        captured["category_id"] = category_id
        captured["limit"] = limit
        captured["platform"] = kwargs.get("platform")
        captured["source"] = kwargs.get("source")
        captured["source_id"] = kwargs.get("source_id")
        return [901], ["celery-901"], 1

    monkeypatch.setattr(
        "app.services.scheduled_tasks.dispatch_update_category",
        fake_dispatch_update_category,
    )

    task_ids = dispatch_scheduled_task(object(), task)

    assert task_ids == [901]
    assert captured == {
        "category_id": 3,
        "limit": 10,
        "platform": "bilibili",
        "source": "scheduled",
        "source_id": 12,
    }
