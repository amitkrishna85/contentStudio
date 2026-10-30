from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from creatoros.app.routes.api import router as api_router
from creatoros.app.routes.ui import router as ui_router

app = FastAPI(title="CreatorOS")
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "static")), name="static")
app.include_router(api_router)
app.include_router(ui_router)


@app.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "pong"}
