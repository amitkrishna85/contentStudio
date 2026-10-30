from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from creatoros.app.db import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    voice_profile_json = Column(Text, nullable=True)
    sample_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    contents = relationship("Content", back_populates="brand")


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    brief = Column(Text, nullable=False)
    platform = Column(String(64), nullable=False)
    strategy_json = Column(Text, nullable=True)
    draft_versions_json = Column(Text, nullable=True)
    final_text = Column(Text, nullable=True)
    image_path = Column(String(255), nullable=True)
    status = Column(String(64), default="draft")
    scheduled_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    editor_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="contents")
    decisions = relationship("Decision", back_populates="content")
    metrics = relationship("Metric", back_populates="content")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    agent = Column(String(128), nullable=False)
    decision_type = Column(String(64), nullable=False)
    summary = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content", back_populates="decisions")


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    impressions = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    source = Column(String(64), default="manual")
    recorded_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content", back_populates="metrics")


class Learning(Base):
    __tablename__ = "learnings"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(Text, nullable=False)
    evidence_content_ids_json = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    recommendation = Column(Text, nullable=True)
    active = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
