from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from google import genai

from creatoros.app.config import settings

client: genai.Client | None = None
GEMINI_REQUEST_TIMEOUT_SECONDS = 60


def _get_client() -> genai.Client:
    """Build the Gemini API client on first use."""
    global client
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to the project .env file and restart CreatorOS.")
    if client is None:
        client = genai.Client(api_key=api_key)
    return client


def is_configured() -> bool:
    """Return whether Gemini credentials are available to this app process."""
    return bool(settings.gemini_api_key or os.getenv("GEMINI_API_KEY"))

def _model_name(model: str | None = None) -> str:
    return model or settings.text_model


def _validate_json_object(payload: Any, schema: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("JSON response must be an object.")
    if schema is None:
        return payload
    required = schema.get("required", [])
    for key in required:
        if key not in payload:
            raise ValueError(f"Missing required field: {key}")
    properties = schema.get("properties", {})
    for key, value in payload.items():
        if key in properties:
            expected = properties[key]
            if isinstance(expected, dict) and expected.get("type") == "array":
                if not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be a list.")
    return payload


def chat(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    json_mode: bool = False,
    response_schema: Mapping[str, Any] | None = None,
) -> str:
    """Return a plain text completion from Gemini."""
    config: dict[str, Any] = {
        "system_instruction": system_prompt,
        "temperature": temperature,
        "http_options": {"timeout": GEMINI_REQUEST_TIMEOUT_SECONDS * 1000},
    }
    if json_mode:
        config["response_mime_type"] = "application/json"
        config["response_json_schema"] = response_schema or {"type": "object"}
    response = _get_client().models.generate_content(
        model=_model_name(model),
        contents=user_prompt,
        config=config,
    )
    content = response.text
    if not content:
        raise ValueError("Gemini API returned an empty text response.")
    return content


def chat_json(
    system_prompt: str,
    user_prompt: str,
    schema: Mapping[str, Any] | None = None,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Return a parsed JSON object, retrying once if the payload looks malformed."""
    try:
        content = chat(
            system_prompt=f"{system_prompt}\nReturn valid JSON only.",
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            json_mode=True,
            response_schema=schema,
        )
        text = content.strip()
        payload = json.loads(text)
        _validate_json_object(payload, schema)
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        retry = chat(
            system_prompt=f"{system_prompt}\nThe previous response was invalid JSON. Return a single valid JSON object only.",
            user_prompt=user_prompt,
            model=model,
            temperature=0.1,
            json_mode=True,
            response_schema=schema,
        )
        text = retry.strip()
        payload = json.loads(text)
        _validate_json_object(payload, schema)
        return payload


def generate_image(prompt: str, model: str | None = None, output_dir: str | None = None) -> str:
    """Generate an image and save it under static/images/. Return the saved path."""
    image_model = model or settings.image_model
    response = _get_client().models.generate_content(
        model=image_model,
        contents=prompt,
        config={
            "response_modalities": ["IMAGE"],
            "http_options": {"timeout": GEMINI_REQUEST_TIMEOUT_SECONDS * 1000},
        },
    )
    image_part = next(
        (
            part
            for part in response.parts or []
            if part.inline_data is not None and part.inline_data.data is not None
        ),
        None,
    )
    image_bytes = image_part.inline_data.data if image_part else None
    if not image_bytes:
        raise ValueError("Gemini API returned no image payload.")

    target_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "static" / "images")
    target_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"image_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.png"
    file_path = target_dir / file_name
    file_path.write_bytes(image_bytes)
    return str(file_path)
