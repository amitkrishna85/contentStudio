from fastapi.testclient import TestClient

from creatoros.app.agents import visual
from creatoros.app.main import app
from creatoros.app.routes import ui


def test_visual_fallback_uses_writable_vercel_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(visual.tempfile, "gettempdir", lambda: str(tmp_path))

    def fail_image_generation(*args, **kwargs):
        raise OSError("Image generation unavailable")

    monkeypatch.setattr(visual, "generate_image", fail_image_generation)

    result = visual.create_visual("A clear security message.")

    assert result["method"] == "fallback"
    assert result["image_path"] == str(tmp_path / "creatoros" / "images" / "fallback_text_card.png")
    assert (tmp_path / "creatoros" / "images" / "fallback_text_card.png").is_file()


def test_generated_image_route_serves_vercel_temporary_image(monkeypatch, tmp_path):
    image_dir = tmp_path / "creatoros" / "images"
    image_dir.mkdir(parents=True)
    image_bytes = b"test-image"
    (image_dir / "generated.png").write_bytes(image_bytes)
    monkeypatch.setattr(ui.tempfile, "gettempdir", lambda: str(tmp_path))

    response = TestClient(app).get("/generated-images/generated.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == image_bytes
