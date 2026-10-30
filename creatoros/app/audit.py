from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from creatoros.app.db import SessionLocal
from creatoros.app.models import Decision


def log_decision(content_id: int | None, agent: str, decision_type: str, summary: str, reasoning: str, payload: dict[str, Any] | None = None) -> Decision:
    """Persist a structured decision record for auditing."""
    db = SessionLocal()
    try:
        record = Decision(
            content_id=content_id,
            agent=agent,
            decision_type=decision_type,
            summary=summary,
            reasoning=reasoning,
            payload_json=json.dumps(payload or {}, default=str),
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()
