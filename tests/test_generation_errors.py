from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
from google.genai._gaos.lib.compat_errors import APITimeoutError, InternalServerError
from google.genai.errors import ClientError
from fastapi.testclient import TestClient

from creatoros.app.main import app
from creatoros.app.routes import ui


def test_missing_gemini_key_is_shown_instead_of_saving_placeholder(monkeypatch):
    monkeypatch.setattr(ui, "is_configured", lambda: False)
    response = TestClient(app).get("/new")
    assert response.status_code == 200
    assert "AI generation is not configured" in response.text
    assert "GEMINI_API_KEY" in response.text


def test_pipeline_failure_is_reported_without_saving_content(monkeypatch):
    def fail_pipeline(*args, **kwargs):
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to the project .env file and restart CreatorOS.")

    monkeypatch.setattr(ui, "run_pipeline", fail_pipeline)
    client = TestClient(app)
    before = client.get("/")
    response = client.post(
        "/new",
        data={"brief": "A usable LinkedIn post about AI safety.", "platform": "LinkedIn", "brand_id": "1"},
    )
    assert response.status_code == 503
    assert "Content was not generated." in response.text
    assert "GEMINI_API_KEY" in response.text
    assert "Here is the core idea" not in response.text
    assert before.status_code == 200


def test_gemini_service_error_is_shown_instead_of_returning_500(monkeypatch):
    def fail_pipeline(*args, **kwargs):
        raise InternalServerError(
            "Service unavailable",
            response=httpx.Response(503, request=httpx.Request("POST", "https://example.test")),
            body={"error": {"message": "Service unavailable"}},
        )

    monkeypatch.setattr(ui, "run_pipeline", fail_pipeline)
    response = TestClient(app).post(
        "/new",
        data={"brief": "A LinkedIn post about AI safety.", "platform": "LinkedIn", "brand_id": "1"},
    )

    assert response.status_code == 503
    assert "Gemini is temporarily unavailable" in response.text


def test_gemini_quota_error_explains_how_to_proceed(monkeypatch):
    def fail_pipeline(*args, **kwargs):
        raise ClientError(
            429,
            {"error": {"message": "Quota exceeded"}},
            response=httpx.Response(429, request=httpx.Request("POST", "https://example.test")),
        )

    monkeypatch.setattr(ui, "run_pipeline", fail_pipeline)
    response = TestClient(app).post(
        "/new",
        data={"brief": "A LinkedIn post about AI safety.", "platform": "LinkedIn", "brand_id": "1"},
    )

    assert response.status_code == 503
    assert "request quota is exhausted" in response.text


def test_gemini_timeout_is_explained_instead_of_returning_generic_error(monkeypatch):
    def fail_pipeline(*args, **kwargs):
        raise APITimeoutError(httpx.Request("POST", "https://example.test"))

    monkeypatch.setattr(ui, "run_pipeline", fail_pipeline)
    response = TestClient(app).post(
        "/new",
        data={"brief": "A LinkedIn post about AI safety.", "platform": "LinkedIn", "brand_id": "1"},
    )

    assert response.status_code == 503
    assert "Gemini took too long to respond" in response.text


def test_generation_does_not_block_health_requests(monkeypatch):
    started = Event()
    finish = Event()

    def slow_pipeline(*args, **kwargs):
        started.set()
        finish.wait(timeout=5)
        raise RuntimeError("Generation test complete.")

    monkeypatch.setattr(ui, "run_pipeline", slow_pipeline)
    client = TestClient(app)
    form = {"brief": "A LinkedIn post about AI safety.", "platform": "LinkedIn", "brand_id": "1"}

    with ThreadPoolExecutor(max_workers=1) as executor:
        generation = executor.submit(client.post, "/new", data=form)
        assert started.wait(timeout=5)
        health = client.get("/ping")
        finish.set()
        response = generation.result(timeout=5)

    assert health.status_code == 200
    assert response.status_code == 503


def test_old_generic_drafts_are_marked_not_publishable():
    assert ui._is_legacy_fallback("Here is the core idea:\nA fake draft.")
    assert not ui._is_legacy_fallback("A genuine post with a clear hook.")
