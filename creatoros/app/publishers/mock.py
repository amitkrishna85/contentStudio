from __future__ import annotations

from datetime import datetime

from creatoros.app.publishers.base import Publisher


class MockPublisher(Publisher):
    """A default mock publisher that records the status flow for content."""

    def publish(self, content_id: int, scheduled_at: datetime) -> dict:
        return {
            "content_id": content_id,
            "status": "published",
            "scheduled_at": scheduled_at.isoformat(),
            "publisher": "mock",
        }
