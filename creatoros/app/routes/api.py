from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from creatoros.app.feedback import simulate_engagement
from creatoros.app.graph import run_pipeline

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/content")
def create_content(payload: dict[str, Any]) -> dict[str, Any]:
    brief = str(payload.get("brief", ""))
    brand_profile = payload.get("brand_profile") or {"tone": "clear and practical"}
    result = run_pipeline(brief, brand_profile=brand_profile)
    return {"brief": brief, "final_draft": result["final_draft"], "strategy": result["strategy"]}


@router.post("/simulate")
def simulate(payload: dict[str, Any]) -> dict[str, Any]:
    brief = str(payload.get("brief", "A practical security post"))
    return simulate_engagement(
        brief,
        hook_style=payload.get("hook_style"),
        length=payload.get("length"),
        angle=payload.get("angle"),
        post_hour=payload.get("post_hour"),
        hashtags=payload.get("hashtags", 0),
    )


@router.get("/content/{content_id}")
def content_detail(content_id: str) -> dict[str, Any]:
    return {"content_id": content_id, "status": "draft"}
