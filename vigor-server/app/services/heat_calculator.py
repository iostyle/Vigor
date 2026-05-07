from datetime import datetime

HALF_LIFE_HOURS = 72.0


def calculate_heat_score(
    like_count: int,
    comment_count: int,
    share_count: int,
    publish_time: datetime,
) -> float:
    likes = max(like_count, 0)
    comments = max(comment_count, 0)
    shares = max(share_count, 0)

    base_score = likes * 1.0 + comments * 2.0 + shares * 5.0

    now = datetime.now(publish_time.tzinfo) if publish_time.tzinfo else datetime.now()
    hours_since_publish = (now - publish_time).total_seconds() / 3600

    if hours_since_publish <= 0:
        decay_factor = 1.0
    else:
        decay_factor = 2 ** (-hours_since_publish / HALF_LIFE_HOURS)

    return round(base_score * decay_factor, 2)
