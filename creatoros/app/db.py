from __future__ import annotations

import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def _database_url() -> URL:
    database = "creatoros.db"
    if os.getenv("VERCEL"):
        database = str(Path(tempfile.gettempdir()) / database)
    return URL.create("sqlite", database=database)


DATABASE_URL = _database_url()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


from creatoros.app import models  # noqa: E402,F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
