"""Lead scoring endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.repositories.lead_repository import LeadRepository
from app.schemas.analysis import ScoringResponse
from app.services.ai_service import AIService
from app.services.scoring_service import ScoringService
from app.utils.helpers import lead_to_context_dict, safe_json_dumps

router = APIRouter(prefix="/score", tags=["Scoring"])


@router.post("/{lead_id}", response_model=ScoringResponse)
async def score_lead(
    lead_id: int,
    use_ai: bool = Query(default=True, description="Use OpenAI for scoring; falls back to heuristics"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Generate an AI lead score (0-100) for the given lead.
    Uses OpenAI by default; pass use_ai=false for heuristic scoring.
    """
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    context = lead_to_context_dict(lead)

    if use_ai:
        try:
            ai_service = AIService()
            result = await ai_service.generate_score(context)
        except Exception:
            # Graceful fallback to heuristic scoring
            result = ScoringService().score(context)
    else:
        result = ScoringService().score(context)

    await repo.save_score(
        lead_id,
        {
            "ai_score": result.ai_score,
            "score_breakdown": safe_json_dumps(result.breakdown.model_dump()),
        },
    )

    return ScoringResponse(lead_id=lead_id, score=result)
