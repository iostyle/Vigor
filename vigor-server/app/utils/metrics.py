from prometheus_client import Counter, Histogram, Gauge

crawl_tasks_total = Counter(
    "crawl_tasks_total", "Total crawl tasks", ["status"]
)
crawl_videos_total = Counter(
    "crawl_videos_total", "Total videos crawled"
)
crawl_duration_seconds = Histogram(
    "crawl_duration_seconds", "Crawl task duration"
)

api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)
api_latency_seconds = Histogram(
    "api_latency_seconds",
    "API request latency",
    ["method", "endpoint"],
)

celery_queue_length = Gauge(
    "celery_queue_length", "Celery queue length", ["queue"]
)

douyin_api_errors_total = Counter(
    "douyin_api_errors_total", "Douyin API errors"
)
douyin_api_rate_limit_hits = Counter(
    "douyin_api_rate_limit_hits", "Douyin API rate limit hits"
)
summary_generation_total = Counter(
    "summary_generation_total",
    "Summary generation attempts",
    ["status"],
)
