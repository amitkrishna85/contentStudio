from __future__ import annotations

from datetime import datetime, timedelta

from creatoros.app.publishers.base import Publisher
from creatoros.app.publishers.mock import MockPublisher


class Scheduler:
    """Simple scheduler wrapper around a publisher interface."""

    def __init__(self, publisher: Publisher | None = None):
        self.publisher = publisher or MockPublisher()

    def schedule_post(self, content_id: int, due_at: datetime | None = None) -> dict:
        post_time = due_at or (datetime.utcnow() + timedelta(hours=1))
        return self.publisher.publish(content_id=content_id, scheduled_at=post_time)

    def schedule_best_hour(self, content_id: int, candidate_hours: list[int] | None = None) -> dict:
        hours = candidate_hours or [9, 10, 11, 18, 19]
        best_hour = max(hours, key=lambda h: 1 if h in {9, 10, 11, 18, 19} else 0)
        scheduled_at = datetime.utcnow().replace(hour=best_hour, minute=0, second=0, microsecond=0)
        if scheduled_at < datetime.utcnow():
            scheduled_at += timedelta(days=1)
        return self.publisher.publish(content_id=content_id, scheduled_at=scheduled_at)
