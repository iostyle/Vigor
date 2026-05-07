from prometheus_client import Counter, Gauge, Histogram

from app.utils import metrics


def test_counters_are_counter_instances():
    assert isinstance(metrics.crawl_tasks_total, Counter)
    assert isinstance(metrics.crawl_videos_total, Counter)
    assert isinstance(metrics.api_requests_total, Counter)
    assert isinstance(metrics.douyin_api_errors_total, Counter)
    assert isinstance(metrics.douyin_api_rate_limit_hits, Counter)
    assert isinstance(metrics.summary_generation_total, Counter)


def test_histograms_are_histogram_instances():
    assert isinstance(metrics.crawl_duration_seconds, Histogram)
    assert isinstance(metrics.api_latency_seconds, Histogram)


def test_gauges_are_gauge_instances():
    assert isinstance(metrics.celery_queue_length, Gauge)


def test_counter_inc_with_labels():
    metrics.crawl_tasks_total.labels(status="success").inc()
    metrics.crawl_tasks_total.labels(status="success").inc(2)
    sample = metrics.crawl_tasks_total.labels(status="success")._value.get()
    assert sample >= 3


def test_counter_inc_without_labels():
    before = metrics.crawl_videos_total._value.get()
    metrics.crawl_videos_total.inc()
    assert metrics.crawl_videos_total._value.get() == before + 1


def test_histogram_observe():
    metrics.crawl_duration_seconds.observe(1.5)
    metrics.api_latency_seconds.labels(
        method="GET", endpoint="/test"
    ).observe(0.25)


def test_gauge_set():
    metrics.celery_queue_length.labels(queue="default").set(10)
    value = metrics.celery_queue_length.labels(queue="default")._value.get()
    assert value == 10


def test_api_requests_counter_with_labels():
    metrics.api_requests_total.labels(
        method="GET", endpoint="/health", status_code="200"
    ).inc()


def test_summary_generation_counter():
    metrics.summary_generation_total.labels(status="success").inc()
    metrics.summary_generation_total.labels(status="failed").inc()
