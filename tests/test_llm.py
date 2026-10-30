import os
from types import SimpleNamespace

import pytest
from google.genai.errors import APIError

from creatoros.app import llm
from creatoros.app.llm import chat, chat_json, generate_image


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not set")
def test_llm_smoke():
    try:
        text = chat("You are a terse assistant.", "Reply with exactly: ok")
    except APIError as exc:
        pytest.skip(f"Gemini API smoke test unavailable: {exc}")
    assert isinstance(text, str)
    assert text.strip()

    payload = chat_json(
        "Return a valid JSON object.",
        "Give a tiny object with name and score.",
        schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "score": {"type": "integer"}},
            "required": ["name", "score"],
        },
    )
    assert isinstance(payload, dict)
    assert {"name", "score"}.issubset(payload.keys())

    image_path = generate_image("A tiny abstract glowing gradient, minimalist")
    assert image_path.endswith(".png")


def test_chat_uses_gemini_generate_content(monkeypatch):
    calls = []
    schema = {
        "type": "object",
        "properties": {"draft": {"type": "string"}},
        "required": ["draft"],
    }
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(text='{"draft":"ok"}')
        )
    )
    monkeypatch.setattr(
        llm,
        "settings",
        SimpleNamespace(
            gemini_api_key="test-key",
            text_model="gemini-test-text",
            judge_model="gemini-test-judge",
            image_model="gemini-test-image",
        ),
    )
    monkeypatch.setattr(llm, "client", None)
    monkeypatch.setattr(llm.genai, "Client", lambda api_key: fake_client)

    result = chat(
        "System instruction",
        "User input",
        temperature=0.3,
        json_mode=True,
        response_schema=schema,
    )

    assert result == '{"draft":"ok"}'
    assert calls == [
        {
            "model": "gemini-test-text",
            "contents": "User input",
            "config": {
                "system_instruction": "System instruction",
                "temperature": 0.3,
                "http_options": {"timeout": llm.GEMINI_REQUEST_TIMEOUT_SECONDS * 1000},
                "response_mime_type": "application/json",
                "response_json_schema": schema,
            },
        }
    ]


def test_generate_image_saves_gemini_output(monkeypatch, tmp_path):
    image_bytes = b"fake-image"
    calls = []
    fake_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: calls.append(kwargs)
            or SimpleNamespace(
                parts=[SimpleNamespace(inline_data=SimpleNamespace(data=image_bytes))]
            )
        )
    )
    monkeypatch.setattr(
        llm,
        "settings",
        SimpleNamespace(
            gemini_api_key="test-key",
            text_model="gemini-test-text",
            judge_model="gemini-test-judge",
            image_model="gemini-test-image",
        ),
    )
    monkeypatch.setattr(llm, "client", fake_client)

    image_path = generate_image("An abstract image", output_dir=str(tmp_path))

    with open(image_path, "rb") as image_file:
        assert image_file.read() == image_bytes
    assert calls == [
        {
            "model": "gemini-test-image",
            "contents": "An abstract image",
            "config": {
                "response_modalities": ["IMAGE"],
                "http_options": {"timeout": llm.GEMINI_REQUEST_TIMEOUT_SECONDS * 1000},
            },
        }
    ]
