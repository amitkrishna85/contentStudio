from pathlib import Path
from tempfile import gettempdir

from creatoros.app.db import Base, _database_url, engine


def test_database_metadata_initializes():
    assert Base.metadata is not None
    assert engine is not None
    assert "brands" in Base.metadata.tables
    assert "content" in Base.metadata.tables
    assert "decisions" in Base.metadata.tables
    assert "metrics" in Base.metadata.tables
    assert "learnings" in Base.metadata.tables


def test_vercel_uses_writable_temporary_sqlite_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert _database_url().database == str(Path(gettempdir()) / "creatoros.db")
