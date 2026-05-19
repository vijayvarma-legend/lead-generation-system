"""Pydantic schemas for analysis, scoring, and personalization responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WebsiteAnalysisResult(BaseModel):
    title: str | None = None
    headings: list[str] = Field(default_factory=list)
    social_links: dict[str, str] = Field(default_factory=dict)
    has_contact_form: bool = False
    has_gallery: bool = False
    is_mobile_responsive: bool = False
    has_modern_ui: bool = False
    website_quality_score: int = Field(default=0, ge=0, le=100)
    website_quality: str = "none"
    analysis_summary: str = ""
    raw_text_snippet: str = ""
    error: str | None = None


class ScoreBreakdown(BaseModel):
    website_existence: int = Field(default=0, ge=0, le=25)
    website_quality: int = Field(default=0, ge=0, le=25)
    reviews_and_rating: int = Field(default=0, ge=0, le=20)
    social_presence: int = Field(default=0, ge=0, le=15)
    mobile_optimization: int = Field(default=0, ge=0, le=15)
    total: int = Field(default=0, ge=0, le=100)
    reasoning: str = ""


class ScoreResult(BaseModel):
    ai_score: int = Field(..., ge=0, le=100)
    breakdown: ScoreBreakdown
    recommendation: str = ""


class OutreachMessages(BaseModel):
    email: str
    whatsapp: str
    dm: str
    primary: str


class PersonalizationResult(BaseModel):
    lead_id: int
    messages: OutreachMessages


class AnalysisResponse(BaseModel):
    lead_id: int
    analysis: WebsiteAnalysisResult
    message: str = "Analysis complete"


class ScoringResponse(BaseModel):
    lead_id: int
    score: ScoreResult
    message: str = "Scoring complete"
