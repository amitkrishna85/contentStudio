from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creatoros.app.llm import chat_json


def load_brand_samples(brand_name: str) -> list[str]:
    """Read all sample posts for a brand from data/samples/<brand_name>."""
    sample_dir = Path(__file__).resolve().parents[2] / "data" / "samples" / brand_name
    if not sample_dir.exists():
        raise FileNotFoundError(f"Sample directory not found: {sample_dir}")
    texts: list[str] = []
    for path in sorted(sample_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if text.strip():
            texts.append(text)
    return texts


def infer_brand_voice(brand_name: str, samples: list[str] | None = None) -> dict[str, Any]:
    """Infer a brand voice profile from sample posts and persist it as JSON."""
    sample_posts = samples if samples is not None else load_brand_samples(brand_name)
    if len(sample_posts) < 5:
        raise ValueError(f"Brand '{brand_name}' needs at least 5 sample posts.")

    prompt = "\n\n---\n\n".join(sample_posts)
    schema = {
        "type": "object",
        "properties": {
            "tone": {"type": "string"},
            "sentence_length": {"type": "string"},
            "vocabulary": {"type": "array"},
            "emoji_habits": {"type": "string"},
            "hashtag_habits": {"type": "string"},
            "formatting_quirks": {"type": "array"},
            "banned_phrases": {"type": "array"},
            "few_shot_exemplars": {"type": "array"},
        },
        "required": [
            "tone",
            "sentence_length",
            "vocabulary",
            "emoji_habits",
            "hashtag_habits",
            "formatting_quirks",
            "banned_phrases",
            "few_shot_exemplars",
        ],
    }

    profile = chat_json(
        system_prompt=(
            "You are a brand voice analyst. Based only on the provided sample posts, infer a concise but actionable brand voice profile. "
            "Return valid JSON matching the schema exactly."
        ),
        user_prompt=(
            f"Brand: {brand_name}\n"
            "Analyze the sample posts and extract the voice profile.\n\n"
            f"Samples:\n{prompt}"
        ),
        schema=schema,
    )

    output_path = Path(__file__).resolve().parents[2] / "data" / "brand_profiles" / f"{brand_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile
