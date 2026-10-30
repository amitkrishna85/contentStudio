from __future__ import annotations

from typing import Any

from creatoros.app.llm import chat_json


def write_draft(
    brief: str,
    strategy: dict[str, Any] | None = None,
    brand_profile: dict[str, Any] | None = None,
    platform: str = "LinkedIn",
    required_edits: list[str] | None = None,
    playbook: str = "",
) -> str:
    """Draft a platform-aware content piece, optionally revising using required edits."""
    if not brief.strip():
        raise ValueError("A content brief is required.")
    strategy = strategy or {}
    platform_instructions = {
        "LinkedIn": (
            "Write a polished LinkedIn post of roughly 120-220 words. Start with a strong first-line hook, "
            "use short readable paragraphs, add one specific useful insight, and end with a natural question or CTA. "
            "Use 0-3 relevant hashtags only when consistent with the brand."
        ),
        "X thread": (
            "Write a 4-7 post X thread. Number each post (1/, 2/, etc.), keep each post concise and below 280 characters, "
            "make the first post a compelling hook, and finish the final post with a clear takeaway or CTA."
        ),
        "Instagram": (
            "Write an Instagram caption with a scroll-stopping first line, concise conversational paragraphs, "
            "a specific CTA, and 3-8 relevant hashtags at the end. Follow the brand's emoji habits."
        ),
    }
    platform_guide = platform_instructions.get(
        platform,
        "Write native-to-platform copy with a strong hook, useful specifics, readable formatting, and a clear CTA.",
    )
    payload = {
        "type": "object",
        "properties": {
            "draft": {"type": "string"},
        },
        "required": ["draft"],
    }
    result = chat_json(
        system_prompt=(
            "You are a senior platform copywriter. Produce final, publication-ready copy, not an outline, analysis, "
            "or explanation of your process. Follow the brief, strategy, brand profile, and learning playbook. "
            "In revision mode, apply every required edit naturally; never print the edit list. Return valid JSON."
        ),
        user_prompt=(
            f"Brief: {brief}\n"
            f"Platform: {platform}\nPlatform conventions: {platform_guide}\n"
            f"Brand voice profile: {brand_profile or {}}\n"
            f"Strategic direction: {strategy}\n"
            f"Performance learnings to apply: {playbook or 'None'}\n"
            f"Required edits for this revision: {required_edits or 'None'}\n"
            "The draft value must contain only copy the user can publish, with platform-appropriate line breaks. "
            "Return JSON with one non-empty 'draft' string."
        ),
        schema=payload,
    )
    draft = str(result.get("draft", "")).strip()
    if not draft:
        raise ValueError("The writer returned an empty draft.")
    return draft
