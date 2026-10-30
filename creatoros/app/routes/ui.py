from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from google.genai._gaos.lib.compat_errors import APITimeoutError, GeminiNextGenAPIClientError
from google.genai.errors import APIError
from sqlalchemy.orm import joinedload
from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse

from creatoros.app.db import SessionLocal, init_db
from creatoros.app.graph import run_pipeline
from creatoros.app.llm import is_configured
from creatoros.app.models import Brand, Content, Decision, Learning

router = APIRouter()
APP_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(APP_ROOT / "templates"))


@router.get("/generated-images/{image_name}")
async def generated_image(image_name: str):
    image_path = Path(tempfile.gettempdir()) / "creatoros" / "images" / Path(image_name).name
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Generated image not found.")
    return FileResponse(image_path, media_type="image/png")


def _is_legacy_fallback(text: str | None) -> bool:
    """Identify drafts persisted by the old generic fallback writer."""
    return bool(text and text.startswith("Here is the core idea:"))


def _ensure_seed_brands(db) -> None:
    init_db()
    for slug, label in (
        ("formal-enterprise", "Northstar Security"),
        ("casual-indie", "Build Calm"),
    ):
        brand = db.query(Brand).filter(Brand.name == label).first()
        if brand is None:
            profile_path = APP_ROOT.parent / "data" / "brand_profiles" / f"{slug}.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            db.add(Brand(name=label, voice_profile_json=json.dumps(profile), sample_count=6))
    db.commit()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = SessionLocal()
    try:
        _ensure_seed_brands(db)
        contents = (
            db.query(Content)
            .options(joinedload(Content.brand))
            .order_by(Content.created_at.desc())
            .limit(8)
            .all()
        )
        brands = db.query(Brand).order_by(Brand.id).all()
        total_posts = db.query(Content).count()
        scheduled = db.query(Content).filter(Content.status == "scheduled").count()
        published = db.query(Content).filter(Content.status == "published").count()
        active_learnings = db.query(Learning).filter(Learning.active == 1).count()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "title": "CreatorOS — Content Studio",
                "contents": contents,
                "legacy_content_ids": {item.id for item in contents if _is_legacy_fallback(item.final_text)},
                "brands": brands,
                "total_posts": total_posts,
                "scheduled": scheduled,
                "published": published,
                "active_learnings": active_learnings,
                "now": datetime.now(timezone.utc),
                "gemini_configured": is_configured(),
            },
        )
    finally:
        db.close()


@router.get("/new", response_class=HTMLResponse)
async def new_brief(request: Request):
    db = SessionLocal()
    try:
        _ensure_seed_brands(db)
        brands = db.query(Brand).order_by(Brand.id).all()
        return templates.TemplateResponse(
            request=request,
            name="new-brief.html",
            context={"title": "Create content", "brands": brands, "gemini_configured": is_configured()},
        )
    finally:
        db.close()


@router.post("/new")
async def create_content_from_brief(request: Request):
    form = parse_qs((await request.body()).decode("utf-8"))
    brief = form.get("brief", [""])[0].strip()
    brand_id = form.get("brand_id", [""])[0]
    platform = form.get("platform", ["LinkedIn"])[0]
    if not brief:
        return RedirectResponse(url="/new?error=brief", status_code=303)

    db = SessionLocal()
    try:
        _ensure_seed_brands(db)
        brand = db.query(Brand).filter(Brand.id == int(brand_id)).first() if brand_id.isdigit() else None
        if brand is None:
            brand = db.query(Brand).order_by(Brand.id).first()
        if brand is None:
            raise RuntimeError("No seeded brands are available.")
        profile = json.loads(brand.voice_profile_json or "{}")
        try:
            pipeline = await run_in_threadpool(run_pipeline, brief, profile, platform=platform)
        except RuntimeError as exc:
            return _render_brief_error(request, db, brief, platform, brand.id, str(exc))
        except (APIError, GeminiNextGenAPIClientError) as exc:
            response = getattr(exc, "response", None)
            status_code = (
                getattr(exc, "code", None)
                or getattr(exc, "status_code", None)
                or getattr(response, "status_code", None)
            )
            detail = f" (HTTP {status_code})" if status_code else ""
            if status_code == 503:
                message = "Gemini is temporarily unavailable. Please wait a moment and try again."
            elif status_code == 504:
                message = "Gemini did not finish before its service deadline. Please retry; the app is configured to use Flash Lite."
            elif status_code == 429:
                message = (
                    "Gemini's request quota is exhausted for the configured model. Wait for the quota to reset, "
                    "or check Google AI Studio billing and limits before trying again."
                )
            elif isinstance(exc, APITimeoutError):
                message = "Gemini took too long to respond. Please try again, or use a faster text model in .env."
            else:
                message = (
                    f"Gemini API request failed{detail}. Check that GEMINI_API_KEY is valid and that the configured "
                    "Gemini models are available to your Google AI Studio project."
                )
            return _render_brief_error(request, db, brief, platform, brand.id, message)
        except (ValueError, json.JSONDecodeError) as exc:
            return _render_brief_error(
                request,
                db,
                brief,
                platform,
                brand.id,
                f"An agent returned an invalid response, so no content was saved: {exc}",
            )
        content = Content(
            brand_id=brand.id,
            brief=brief,
            platform=platform,
            strategy_json=json.dumps(pipeline["strategy"]),
            draft_versions_json=json.dumps(pipeline["draft_versions"]),
            final_text=pipeline["final_draft"],
            image_path=pipeline["visual"]["image_path"],
            status="draft",
            editor_score=float(pipeline["editor_result"].get("overall", 0)),
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        content_id = content.id
        decision_rows = [
            Decision(
                content_id=content_id,
                agent="strategist",
                decision_type="angle",
                summary=str(pipeline["strategy"].get("angle", "Strategy selected")),
                reasoning=str(pipeline["strategy"].get("reasoning", "")),
                payload_json=json.dumps(pipeline["strategy"]),
            ),
            Decision(
                content_id=content_id,
                agent="editor",
                decision_type="edit",
                summary=str(pipeline["editor_result"].get("verdict", "Draft reviewed")),
                reasoning="Editor scores and required edits are recorded with this review.",
                payload_json=json.dumps(pipeline["editor_result"]),
            ),
        ]
        for index, draft in enumerate(pipeline["draft_versions"][1:], start=1):
            from creatoros.app.graph import compute_diff_ratio

            decision_rows.append(
                Decision(
                    content_id=content_id,
                    agent="writer",
                    decision_type="edit",
                    summary=f"Revision {index}: changed {compute_diff_ratio(pipeline['draft_versions'][index - 1], draft):.0%} of the draft",
                    reasoning="Revised in response to the editor's required edits.",
                    payload_json=json.dumps({"draft_version": index + 1}),
                )
            )
        if pipeline["visual"]["method"] == "fallback":
            decision_rows.append(
                Decision(
                    content_id=content_id,
                    agent="visual",
                    decision_type="fallback",
                    summary="Generated a text-card visual because image generation was unavailable.",
                    reasoning="The visual step fell back to a local Pillow-rendered card.",
                    payload_json=json.dumps(pipeline["visual"]),
                )
            )
        db.add_all(decision_rows)
        db.commit()
        return RedirectResponse(url=f"/content/{content_id}", status_code=303)
    finally:
        db.close()


def _render_brief_error(request: Request, db, brief: str, platform: str, brand_id: int, message: str):
    brands = db.query(Brand).order_by(Brand.id).all()
    return templates.TemplateResponse(
        request=request,
        name="new-brief.html",
        context={
            "title": "Create content",
            "brands": brands,
            "gemini_configured": is_configured(),
            "generation_error": message,
            "brief_value": brief,
            "selected_platform": platform,
            "selected_brand_id": brand_id,
        },
        status_code=503,
    )


@router.post("/content/{content_id}/schedule")
async def schedule_content(content_id: int):
    db = SessionLocal()
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if content is None:
            return RedirectResponse(url="/", status_code=303)
        if _is_legacy_fallback(content.final_text):
            return RedirectResponse(url=f"/content/{content_id}?error=legacy", status_code=303)
        content.status = "scheduled"
        content.scheduled_at = datetime.utcnow() + timedelta(hours=1)
        db.add(
            Decision(
                content_id=content.id,
                agent="scheduler",
                decision_type="schedule",
                summary="Scheduled for the next available publishing window.",
                reasoning="A near-term default schedule was selected for this draft.",
                payload_json=json.dumps({"scheduled_at": content.scheduled_at.isoformat()}),
            )
        )
        db.commit()
        return RedirectResponse(url=f"/content/{content_id}", status_code=303)
    finally:
        db.close()


@router.get("/content/{content_id}", response_class=HTMLResponse)
async def content_detail(request: Request, content_id: int):
    db = SessionLocal()
    try:
        content = (
            db.query(Content)
            .options(joinedload(Content.brand))
            .filter(Content.id == content_id)
            .first()
        )
        if content is None:
            return RedirectResponse(url="/", status_code=303)
        decisions = (
            db.query(Decision)
            .filter(Decision.content_id == content.id)
            .order_by(Decision.created_at.asc(), Decision.id.asc())
            .all()
        )
        drafts = json.loads(content.draft_versions_json or "[]")
        strategy = json.loads(content.strategy_json or "{}")
        editor_decision = next((decision for decision in decisions if decision.agent == "editor"), None)
        editor_result = json.loads(editor_decision.payload_json or "{}") if editor_decision else {}
        image_name = Path(content.image_path).name if content.image_path else None
        image_url = (
            f"/generated-images/{image_name}"
            if image_name and os.getenv("VERCEL")
            else f"/static/images/{image_name}" if image_name else None
        )
        return templates.TemplateResponse(
            request=request,
            name="content-detail.html",
            context={
                "content": content,
                "drafts": drafts,
                "strategy": strategy,
                "decisions": decisions,
                "image_url": image_url,
                "editor_result": editor_result,
                "editor_scores": editor_result.get("scores", {}),
                "legacy_placeholder": _is_legacy_fallback(content.final_text),
            },
        )
    finally:
        db.close()
