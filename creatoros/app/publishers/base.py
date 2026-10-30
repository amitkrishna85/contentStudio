from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class Publisher(ABC):
    """Interface for publishing scheduled content."""

    @abstractmethod
    def publish(self, content_id: int, scheduled_at: datetime) -> dict:
        raise NotImplementedError
