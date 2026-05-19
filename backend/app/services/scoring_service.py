"""Rule-based + AI lead scoring service."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.schemas.analysis import ScoreBreakdown, ScoreResult

logger = get_logger(__name__)


class ScoringService:
    """Heuristic lead scorer — used as fallback or standalone without OpenAI."""

    def score(self, lead_data: dict[str, Any]) -> ScoreResult:
        has_website = lead_data.get("has_website", False)
        quality_score = lead_data.get("website_quality_score") or 0
        reviews_count = lead_data.get("reviews_count") or 0
        rating = lead_data.get("rating") or 0.0
        instagram = lead_data.get("instagram")
        facebook = lead_data.get("facebook")
        is_mobile = lead_data.get("is_mobile_responsive")
        has_contact = lead_data.get("has_contact_form")

        # --- website_existence (0-25) ---
        # No website → high opportunity → high score
        if not has_website:
            website_existence = 25
        elif quality_score < 40:
            website_existence = 15
        elif quality_score < 70:
            website_existence = 5
        else:
            website_existence = 0

        # --- website_quality (0-25) ---
        if not has_website:
            website_quality = 25
        else:
            website_quality = max(0, 25 - int(quality_score / 4))

        # --- reviews_and_rating (0-20) ---
        if reviews_count == 0:
            reviews_score = 20
        elif reviews_count < 10:
            reviews_score = 15
        elif reviews_count < 50:
            reviews_score = 10
        elif reviews_count < 200:
            reviews_score = 5
        else:
            reviews_score = 0

        if rating and rating >= 4.5:
            reviews_score = max(0, reviews_score - 5)

        # --- social_presence (0-15) ---
        social_count = sum([bool(instagram), bool(facebook)])
        social_score = max(0, 15 - social_count * 7)

        # --- mobile_optimization (0-15) ---
        if is_mobile is False:
            mobile_score = 15
        elif is_mobile is None and has_website:
            mobile_score = 8
        else:
            mobile_score = 0

        total = website_existence + website_quality + reviews_score + social_score + mobile_score
        total = min(total, 100)

        breakdown = ScoreBreakdown(
            website_existence=website_existence,
            website_quality=website_quality,
            reviews_and_rating=reviews_score,
            social_presence=social_score,
            mobile_optimization=mobile_score,
            total=total,
            reasoning=self._build_reasoning(lead_data, total),
        )

        recommendation = self._recommendation(total)
        logger.debug("Lead scored", business=lead_data.get("business_name"), score=total)

        return ScoreResult(
            ai_score=total,
            breakdown=breakdown,
            recommendation=recommendation,
        )

    @staticmethod
    def _build_reasoning(data: dict[str, Any], total: int) -> str:
        parts = []
        if not data.get("has_website"):
            parts.append("no website detected (high opportunity)")
        if data.get("is_mobile_responsive") is False:
            parts.append("website not mobile-friendly")
        if not data.get("has_contact_form"):
            parts.append("missing contact form")
        reviews = data.get("reviews_count") or 0
        if reviews < 20:
            parts.append(f"low review count ({reviews})")
        return "; ".join(parts) if parts else "standard lead profile"

    @staticmethod
    def _recommendation(score: int) -> str:
        if score >= 75:
            return "High-priority lead — reach out immediately with a website offer."
        if score >= 50:
            return "Good opportunity — pitch mobile optimisation or review management."
        if score >= 25:
            return "Medium priority — offer social media setup or SEO audit."
        return "Low priority — business already has strong digital presence."
