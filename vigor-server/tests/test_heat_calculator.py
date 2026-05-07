import importlib
from datetime import datetime, timedelta

import pytest

BASE_NOW = datetime(2026, 5, 7, 12, 0, 0)


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(BASE_NOW.timestamp(), tz=tz)


@pytest.fixture
def calculator(monkeypatch):
    module = importlib.import_module("app.services.heat_calculator")
    monkeypatch.setattr(module, "datetime", FixedDateTime)
    return module.calculate_heat_score


def test_basic_calculation(calculator):
    publish_time = BASE_NOW

    score = calculator(10, 5, 2, publish_time)

    assert score == 30.0


def test_zero_counts(calculator):
    publish_time = BASE_NOW

    score = calculator(0, 0, 0, publish_time)

    assert score == 0.0


def test_negative_counts(calculator):
    publish_time = BASE_NOW

    score = calculator(-10, 2, -3, publish_time)

    assert score == 4.0


def test_recent_publish(calculator):
    publish_time = BASE_NOW - timedelta(hours=1)

    score = calculator(100, 0, 0, publish_time)

    assert 99.0 < score < 100.0


def test_old_publish(calculator):
    publish_time = BASE_NOW - timedelta(hours=72)

    score = calculator(100, 0, 0, publish_time)

    assert score == 50.0


def test_very_old_publish(calculator):
    publish_time = BASE_NOW - timedelta(days=30)

    score = calculator(100, 0, 0, publish_time)

    assert score < 1.0


def test_future_publish(calculator):
    publish_time = BASE_NOW + timedelta(hours=1)

    score = calculator(10, 5, 2, publish_time)

    assert score == 30.0


def test_comparison(calculator):
    new_video = calculator(20, 5, 2, BASE_NOW - timedelta(hours=2))
    old_video = calculator(80, 0, 0, BASE_NOW - timedelta(days=10))

    assert new_video > old_video
