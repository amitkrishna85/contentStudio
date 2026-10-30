from creatoros.app.db import Base, engine


def test_database_metadata_initializes():
    assert Base.metadata is not None
    assert engine is not None
    assert "brands" in Base.metadata.tables
    assert "content" in Base.metadata.tables
    assert "decisions" in Base.metadata.tables
    assert "metrics" in Base.metadata.tables
    assert "learnings" in Base.metadata.tables
