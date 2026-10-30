from __future__ import annotations

from typing import Any

from creatoros.app.llm import chat_json


def strategize(brief: str, brand_profile: dict[str, Any] | None = None, playbook: str = "") -> dict[str, Any]:
    """Generate a strategic brief for a piece of content."""
    return chat_json(
        system_prompt=(
            "You are a content strategist, not a copywriter. Choose a distinctive, audience-relevant angle; "
            "avoid generic advice. Ground the recommendation in the supplied brand voice and performance playbook."
        ),
        user_prompt=(
            f"Brief: {brief}\nBrand voice profile: {brand_profile or {}}\nLearnings playbook: {playbook or 'None'}\n"
            "Return JSON with angle, hook_style, audience, key_points, platform_notes, reasoning."
        ),
        schema={
            "type": "object",
            "properties": {
                "angle": {"type": "string"},
                "hook_style": {"type": "string"},
                "audience": {"type": "string"},
                "key_points": {"type": "array"},
                "platform_notes": {"type": "string"},
                "reasoning": {"type": "string"},
            },
            "required": ["angle", "hook_style", "audience", "key_points", "platform_notes", "reasoning"],
        },
    )
