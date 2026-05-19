"""Outreach personalization endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.repositories.lead_repository import LeadRepository
from app.schemas.analysis import PersonalizationResult
from app.services.ai_service import AIService
from app.utils.helpers import lead_to_context_dict

router = APIRouter(prefix="/personalize", tags=["Personalization"])


@router.post("/{lead_id}", response_model=PersonalizationResult)
async def personalize_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Generate personalized email, WhatsApp, and cold DM outreach messages
    for the given lead using OpenAI.
    """
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    context = lead_to_context_dict(lead)
    ai_service = AIService()

    messages = await ai_service.generate_outreach(context)

    await repo.save_outreach(
        lead_id,
        {
            "email": messages.email,
            "whatsapp": messages.whatsapp,
            "dm": messages.dm,
        },
    )

    return PersonalizationResult(lead_id=lead_id, messages=messages)
