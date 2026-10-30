from __future__ import annotations

import json
from pathlib import Path

from creatoros.app.db import init_db
from creatoros.app.models import Brand
from creatoros.app.db import SessionLocal


def seed_demo_brands() -> None:
    init_db()
    db = SessionLocal()
    try:
        for name in ["formal-enterprise", "casual-indie"]:
            existing = db.query(Brand).filter(Brand.name == name).first()
            if existing:
                continue
            profile_path = Path(__file__).resolve().parents[1] / "data" / "brand_profiles" / f"{name}.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            brand = Brand(name=name, voice_profile_json=json.dumps(profile), sample_count=6)
            db.add(brand)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_brands()
