"""Pydantic schemas for Lead CRUD and filtering."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.lead import LeadStatus, WebsiteQuality


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class LeadCreate(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    instagram: str | None = None
    facebook: str | None = None
    google_maps_url: str | None = None
    place_id: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    reviews_count: int | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    source_keyword: str | None = None
    source_latitude: float | None = None
    source_longitude: float | None = None
    source_radius: int | None = None

    @field_validator("website", mode="before")
    @classmethod
    def normalise_website(cls, v: str | None) -> str | None:
        if not v:
            return None
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            v = f"https://{v}"
        return v or None


class LeadUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    rating: float | None = Field(default=None, ge=0, le=5)
    reviews_count: int | None = Field(default=None, ge=0)


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class LeadRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    business_name: str
    category: str | None
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    has_website: bool
    instagram: str | None
    facebook: str | None
    google_maps_url: str | None
    place_id: str | None
    rating: float | None
    reviews_count: int | None
    latitude: float | None
    longitude: float | None
    status: LeadStatus
    ai_score: int | None
    score_breakdown: str | None
    website_quality: WebsiteQuality | None
    website_quality_score: int | None
    website_title: str | None
    has_contact_form: bool | None
    has_gallery: bool | None
    is_mobile_responsive: bool | None
    has_modern_ui: bool | None
    website_analysis_summary: str | None
    outreach_email: str | None
    outreach_whatsapp: str | None
    outreach_dm: str | None
    outreach_message: str | None
    source_keyword: str | None
    created_at: datetime
    updated_at: datetime
    analyzed_at: datetime | None
    scored_at: datetime | None
    personalized_at: datetime | None


class LeadSummary(BaseModel):
    """Lightweight projection for list views."""

    model_config = {"from_attributes": True}

    id: int
    business_name: str
    category: str | None
    address: str | None
    phone: str | None
    email: str | None
    website: str | None
    has_website: bool
    rating: float | None
    reviews_count: int | None
    status: LeadStatus
    ai_score: int | None
    website_quality: WebsiteQuality | None
    outreach_email: str | None
    outreach_whatsapp: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Collection request
# ---------------------------------------------------------------------------

class LeadCollectionRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius: int = Field(default=5000, ge=100, le=50000, description="Radius in metres")
    max_results: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Filter / sort
# ---------------------------------------------------------------------------

SortField = Literal[
    "id", "business_name", "ai_score", "rating", "reviews_count", "created_at", "updated_at"
]
SortOrder = Literal["asc", "desc"]


class LeadFilterParams(BaseModel):
    search: str | None = None
    category: str | None = None
    status: LeadStatus | None = None
    has_website: bool | None = None
    min_score: int | None = Field(default=None, ge=0, le=100)
    max_score: int | None = Field(default=None, ge=0, le=100)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    sort_by: SortField = "created_at"
    sort_order: SortOrder = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
