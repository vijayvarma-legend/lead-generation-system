"""Website analysis endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.repositories.lead_repository import LeadRepository
from app.schemas.analysis import AnalysisResponse, WebsiteAnalysisResult
from app.services.website_analysis_service import WebsiteAnalysisService

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/{lead_id}", response_model=AnalysisResponse)
async def analyse_lead_website(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Analyse the website for a given lead using Playwright.
    Updates lead record with analysis results.
    """
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    if not lead.website:
        return AnalysisResponse(
            lead_id=lead_id,
            analysis=WebsiteAnalysisResult(
                error="Lead has no website to analyse",
                website_quality="none",
            ),
            message="No website URL available",
        )

    service = WebsiteAnalysisService()
    result = await service.analyse(lead.website)

    # Persist analysis results
    await repo.save_analysis(
        lead_id,
        {
            "website_title": result.title,
            "has_contact_form": result.has_contact_form,
            "has_gallery": result.has_gallery,
            "is_mobile_responsive": result.is_mobile_responsive,
            "has_modern_ui": result.has_modern_ui,
            "website_quality_score": result.website_quality_score,
            "website_quality": result.website_quality,
            "website_analysis_summary": result.analysis_summary,
            "instagram": (
                result.social_links.get("instagram") or lead.instagram
            ),
            "facebook": (
                result.social_links.get("facebook") or lead.facebook
            ),
        },
    )

    return AnalysisResponse(lead_id=lead_id, analysis=result)


@router.post("/{lead_id}/async", status_code=status.HTTP_202_ACCEPTED)
async def analyse_lead_website_async(
    lead_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Fire-and-forget website analysis — returns immediately."""
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    if not lead.website:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead has no website URL",
        )

    async def _run_analysis():
        async with AsyncSessionLocal() as session:  # noqa: F821
            _repo = LeadRepository(session)
            service = WebsiteAnalysisService()
            result = await service.analyse(lead.website)
            await _repo.save_analysis(lead_id, {
                "website_title": result.title,
                "has_contact_form": result.has_contact_form,
                "has_gallery": result.has_gallery,
                "is_mobile_responsive": result.is_mobile_responsive,
                "has_modern_ui": result.has_modern_ui,
                "website_quality_score": result.website_quality_score,
                "website_quality": result.website_quality,
                "website_analysis_summary": result.analysis_summary,
            })
            await session.commit()

    background_tasks.add_task(_run_analysis)
    return {"message": "Analysis queued", "lead_id": lead_id}
