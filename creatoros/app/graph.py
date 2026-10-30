from __future__ import annotations

import difflib
import json
from typing import Any

from creatoros.app.agents.editor import edit_and_score
from creatoros.app.agents.strategist import strategize
from creatoros.app.agents.visual import create_visual
from creatoros.app.agents.writer import write_draft

REVISION_THRESHOLD = 7
MAX_REVISIONS = 2


def load_brand_voice(brand_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a brand voice profile; this is the first node in a generation graph."""
    return brand_profile or {"tone": "clear and practical", "banned_phrases": []}


def load_learnings(playbook: str = "") -> str:
    """Return the active learning playbook as a plain string."""
    return playbook or "Use a direct hook and keep the post focused on practical value."


def compute_diff_ratio(old_text: str, new_text: str) -> float:
    """Compare two draft versions using difflib and return a ratio in [0, 1]."""
    if old_text == new_text:
        return 0.0
    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    return round(matcher.ratio(), 4)


def route_after_editor(editor_result: dict[str, Any], revisions: int) -> str:
    """Return whether the workflow should revise or move to the visual stage."""
    overall = int(editor_result.get("overall", 0))
    if overall < REVISION_THRESHOLD and revisions < MAX_REVISIONS:
        return "writer"
    return "visual"


def run_pipeline(
    brief: str,
    brand_profile: dict[str, Any] | None = None,
    playbook: str = "",
    platform: str = "LinkedIn",
) -> dict[str, Any]:
    """Run the main generation graph for a brief."""
    brand = load_brand_voice(brand_profile)
    playbook_text = load_learnings(playbook)
    strategy = strategize(brief, brand, playbook_text)
    current_draft = write_draft(brief, strategy, brand, platform=platform, playbook=playbook_text)
    versions = [current_draft]
    revisions = 0
    editor_result = edit_and_score(current_draft, brief, brand)
    while route_after_editor(editor_result, revisions) == "writer":
        revisions += 1
        required = editor_result.get("required_edits", [])
        updated = write_draft(
            brief,
            strategy,
            brand,
            platform=platform,
            required_edits=required,
            playbook=playbook_text,
        )
        versions.append(updated)
        current_draft = updated
        editor_result = edit_and_score(current_draft, brief, brand)
    visual_result = create_visual(current_draft, brand)
    return {
        "brand_profile": brand,
        "strategy": strategy,
        "draft_versions": versions,
        "final_draft": current_draft,
        "editor_result": editor_result,
        "visual": visual_result,
        "diff_ratio": compute_diff_ratio(versions[-2], versions[-1]) if len(versions) > 1 else 0.0,
        "revisions": revisions,
    }
