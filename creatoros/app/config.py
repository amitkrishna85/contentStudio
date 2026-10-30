from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None = None
    text_model: str = "gemini-3.5-flash-lite"
    judge_model: str = "gemini-3.5-flash-lite"
    image_model: str = "gemini-nano-banana-2.1"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            text_model=os.getenv("GEMINI_TEXT_MODEL", "gemini-3.5-flash-lite"),
            judge_model=os.getenv("GEMINI_JUDGE_MODEL", "gemini-3.5-flash-lite"),
            image_model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-nano-banana-2.1"),
        )


settings = Settings.from_env()
