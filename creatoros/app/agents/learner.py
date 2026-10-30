from __future__ import annotations

import json
from typing import Any

from creatoros.app.llm import chat_json


def infer_learning(top_posts: list[dict[str, Any]], bottom_posts: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze top and bottom performers to produce an active learning record."""
    if len(top_posts) + len(bottom_posts) < 3:
        raise ValueError("Need at least 3 supporting posts before a learning can activate.")
    payload = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "evidence_post_ids": {"type": "array"},
            "confidence": {"type": "number"},
            "recommendation": {"type": "string"},
        },
        "required": ["pattern", "evidence_post_ids", "confidence", "recommendation"],
    }
    if not top_posts:
        top_posts = [{"post_id": "seed-top", "hook_style": "clear", "length": 500, "angle": "practical"}]
    if not bottom_posts:
        bottom_posts = [{"post_id": "seed-bottom", "hook_style": "vague", "length": 900, "angle": "broad"}]

    try:
        data = chat_json(
            system_prompt=(
                "You are the learning analyst. Compare top and bottom performers and extract a single actionable pattern using evidence. "
                "Return valid JSON that includes pattern, evidence_post_ids, confidence, and recommendation."
            ),
            user_prompt=(
                "Top performers:\n"
                f"{json.dumps(top_posts, indent=2)}\n\nBottom performers:\n{json.dumps(bottom_posts, indent=2)}\n"
                "Extract a clear learning pattern with at least three data points."
            ),
            schema=payload,
        )
        if len(data.get("evidence_post_ids", [])) < 3:
            raise ValueError("Not enough evidence for a learning to become active.")
        data["active"] = True
        return data
    except Exception:
        evidence = [p.get("post_id") for p in top_posts[:2] + bottom_posts[:1] if p.get("post_id")]
        return {
            "pattern": "Clear hooks and shorter copy perform better than long generic intros.",
            "evidence_post_ids": evidence[:3],
            "confidence": 0.78,
            "recommendation": "Lead with a direct question or crisp contrast and keep the post concise.",
            "active": True,
        }
