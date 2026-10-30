import json
from pathlib import Path

from creatoros.app.brand.voice import load_brand_samples


def test_sample_directory_has_six_posts_per_brand():
    root = Path(__file__).resolve().parents[1] / "creatoros" / "data" / "samples"
    for brand in ["formal-enterprise", "casual-indie"]:
        posts = load_brand_samples(brand)
        assert len(posts) >= 5
        assert all(post.strip() for post in posts)

    formal = root / "formal-enterprise"
    casual = root / "casual-indie"
    assert len(list(formal.glob("*.md"))) >= 6
    assert len(list(casual.glob("*.md"))) >= 6

    profile = json.loads((Path(__file__).resolve().parents[1] / "creatoros" / "data" / "brand_profiles" / "formal-enterprise.json").read_text())
    assert "tone" in profile
    assert "few_shot_exemplars" in profile
