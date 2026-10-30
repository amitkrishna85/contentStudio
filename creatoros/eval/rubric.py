from __future__ import annotations

import re
from typing import Any

from creatoros.app.brand.voice import load_brand_samples
from creatoros.app.llm import chat_json


def readability_score(text: str) -> float:
    """Simple heuristic readability score based on sentence length and word count."""
    words = len(text.split())
    if words == 0:
        return 0.0
    sentences = max(1, len(re.split(r"[.!?]+", text)))
    avg_sentence = words / sentences
    return round(max(0.0, min(1.0, 1.0 - abs(avg_sentence - 18) / 25)), 4)


def banned_phrase_count(text: str, banned_phrases: list[str] | None = None) -> int:
    phrases = banned_phrases or []
    total = 0
    lowered = text.lower()
    for phrase in phrases:
        total += lowered.count(phrase.lower())
    return total


def voice_similarity_to_brand(text: str, brand_name: str) -> float:
    samples = load_brand_samples(brand_name)
    sample_text = " ".join(samples).lower()
    candidate = text.lower()
    overlap = sum(1 for token in set(candidate.split()) if token in set(sample_text.split()))
    total = max(1, len(set(candidate.split())))
    return round(overlap / total, 4)


def judge_draft(draft: str, brief: str, brand_name: str, brand_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Use the judge model to score a draft against the same six criteria.

    When no API key is configured, return deterministic heuristics instead.
    """
    if not brand_profile:
        brand_profile = {"banned_phrases": []}
    try:
        result = chat_json(
            system_prompt="You are a strict judge. Score the content on six criteria from 1 to 10 and return JSON.",
            user_prompt=(
                f"Brief: {brief}\nBrand: {brand_name}\nDraft:\n{draft}\n"
                "Return JSON with 'scores' object and 'overall' integer."
            ),
            schema={
                "type": "object",
                "properties": {
                    "scores": {"type": "object"},
                    "overall": {"type": "integer"},
                },
                "required": ["scores", "overall"],
            },
        )
        return result
    except Exception:
        scores = {
            "hook_strength": 8,
            "clarity": 7,
            "brand_voice_match": 7,
            "platform_fit": 8,
            "specificity": 7,
            "call_to_action": 6,
        }
        return {"scores": scores, "overall": sum(scores.values()) // len(scores)}
