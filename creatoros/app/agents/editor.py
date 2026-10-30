from __future__ import annotations

from typing import Any

from creatoros.app.llm import chat_json


def edit_and_score(draft: str, brief: str, brand_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score a draft against six criteria and produce required edits."""
    payload = {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": {
                    "hook_strength": {"type": "integer"},
                    "clarity": {"type": "integer"},
                    "brand_voice_match": {"type": "integer"},
                    "platform_fit": {"type": "integer"},
                    "specificity": {"type": "integer"},
                    "call_to_action": {"type": "integer"},
                },
                "required": [
                    "hook_strength",
                    "clarity",
                    "brand_voice_match",
                    "platform_fit",
                    "specificity",
                    "call_to_action",
                ],
            },
            "overall": {"type": "integer"},
            "required_edits": {"type": "array"},
            "verdict": {"type": "string"},
        },
        "required": ["scores", "overall", "required_edits", "verdict"],
    }
    result = chat_json(
        system_prompt=(
            "You are an exacting content editor, not the writer. Independently assess the draft against the brief "
            "and brand voice. Score six criteria from 1-10, average them for overall, and provide concrete edits "
            "only where useful. A revision is successful only if its required edits are actually applied."
        ),
        user_prompt=(
            f"Brief: {brief}\nBrand voice profile: {brand_profile or {}}\nDraft:\n{draft}\n"
            "Return JSON with scores, overall, required_edits, and verdict."
        ),
        schema=payload,
    )
    if not 1 <= int(result["overall"]) <= 10:
        raise ValueError("The editor returned an overall score outside the 1-10 range.")
    return result
