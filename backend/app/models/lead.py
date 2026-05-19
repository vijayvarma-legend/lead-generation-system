"""SQLAlchemy ORM model for business leads."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LeadStatus(str, enum.Enum):
    NEW = "new"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    SCORED = "scored"
    PERSONALIZED = "personalized"
    CONTACTED = "contacted"
    CONVERTED = "converted"
    REJECTED = "rejected"


class WebsiteQuality(str, enum.Enum):
    NONE = "none"
    POOR = "poor"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Business identity
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Online presence
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    has_website: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    instagram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Ratings
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Workflow state
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True
    )

    # AI scoring
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Website analysis
    website_quality: Mapped[WebsiteQuality | None] = mapped_column(
        Enum(WebsiteQuality), nullable=True
    )
    website_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100
    website_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    has_contact_form: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_gallery: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_mobile_responsive: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_modern_ui: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    website_analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outreach
    outreach_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_whatsapp: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_dm: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_message: Mapped[str | None] = mapped_column(Text, nullable=True)  # primary

    # Source metadata
    source_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_radius: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    personalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_leads_category_status", "category", "status"),
        Index("ix_leads_ai_score", "ai_score"),
        Index("ix_leads_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Lead id={self.id} name={self.business_name!r} status={self.status}>"
