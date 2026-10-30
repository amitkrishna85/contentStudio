from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from creatoros.app.llm import chat, generate_image


def build_image_prompt(final_text: str, brand_profile: dict | None = None) -> str:
    """Generate a concise image prompt from final copy."""
    brand = brand_profile or {"tone": "professional", "emoji_habits": "none"}
    return (
        f"Create a polished visual for a {brand.get('tone', 'professional')} brand. "
        f"Motif: editorial, modern, clean, minimal. "
        f"Text theme: '{final_text[:80]}' with a strong headline, abstract geometric shapes, soft lighting, premium composition."
    )


def create_visual(final_text: str, brand_profile: dict | None = None, output_dir: str | None = None) -> dict:
    """Create a visual asset, falling back to a text card if generation fails."""
    prompt = build_image_prompt(final_text, brand_profile)
    target_dir = Path(output_dir or Path(__file__).resolve().parents[2] / "static" / "images")
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        image_path = generate_image(prompt, output_dir=str(target_dir))
        return {"image_path": image_path, "method": "generated"}
    except Exception:
        width, height = 1200, 675
        im = Image.new("RGB", (width, height), color=(248, 250, 252))
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=30, outline=(15, 23, 42), width=3)
        body = final_text[:220]
        lines = []
        current = ""
        for token in body.split():
            candidate = f"{current} {token}".strip()
            if len(candidate) < 32:
                current = candidate
            else:
                lines.append(current)
                current = token
        if current:
            lines.append(current)
        for idx, line in enumerate(lines[:6]):
            y = 120 + idx * 60
            draw.text((80, y), line[:48], fill=(15, 23, 42), font=ImageFont.load_default())
        fallback_path = target_dir / "fallback_text_card.png"
        im.save(fallback_path)
        return {"image_path": str(fallback_path), "method": "fallback"}
