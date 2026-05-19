"""General-purpose utility functions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return "{}"


def safe_json_loads(s: str | None) -> Any:
    if not s:
        return {}
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}


def truncate(text: str | None, max_length: int = 100) -> str:
    if not text:
        return ""
    return text if len(text) <= max_length else text[:max_length] + "…"


def lead_to_context_dict(lead: Any) -> dict[str, Any]:
    """Convert ORM Lead into a plain dict for AI prompt context."""
    return {
        "business_name": lead.business_name,
        "category": lead.category,
        "address": lead.address,
        "phone": lead.phone,
        "website": lead.website,
        "has_website": lead.has_website,
        "instagram": lead.instagram,
        "facebook": lead.facebook,
        "rating": float(lead.rating) if lead.rating else None,
        "reviews_count": lead.reviews_count,
        "has_contact_form": lead.has_contact_form,
        "has_gallery": lead.has_gallery,
        "is_mobile_responsive": lead.is_mobile_responsive,
        "has_modern_ui": lead.has_modern_ui,
        "website_quality_score": lead.website_quality_score,
        "website_analysis_summary": lead.website_analysis_summary,
    }
