"""Lead CRUD and collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.repositories.lead_repository import LeadRepository
from app.schemas.common import PaginatedResponse
from app.schemas.lead import (
    LeadCollectionRequest,
    LeadCreate,
    LeadFilterParams,
    LeadRead,
    LeadStatusUpdate,
    LeadSummary,
    LeadUpdate,
    SortField,
    SortOrder,
)
from app.models.lead import Lead
from app.services.lead_collection_service import LeadCollectionService
from app.services.scoring_service import ScoringService
from app.services.website_analysis_service import WebsiteAnalysisService
from app.utils.helpers import lead_to_context_dict, safe_json_dumps

router = APIRouter(prefix="/leads", tags=["Leads"])


def _repo(db: AsyncSession = Depends(get_db)) -> LeadRepository:
    return LeadRepository(db)


# ---------------------------------------------------------------------------
# Collection (Apify integration)
# ---------------------------------------------------------------------------

@router.post("/collect", status_code=status.HTTP_202_ACCEPTED)
async def collect_leads(
    payload: LeadCollectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Trigger Apify Google Maps scraper and persist discovered leads."""
    service = LeadCollectionService()
    repo = LeadRepository(db)

    leads_data = await service.collect(
        keyword=payload.keyword,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius=payload.radius,
        max_results=payload.max_results,
    )
    saved = await repo.bulk_create(leads_data)
    await db.commit()

    return {
        "message": f"Collected and saved {len(saved)} leads",
        "total_found": len(leads_data),
        "new_leads": len(saved),
        "keyword": payload.keyword,
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    repo: LeadRepository = Depends(_repo),
    _: str = Depends(verify_api_key),
):
    lead = await repo.create(payload)
    return lead


@router.get("", response_model=PaginatedResponse[LeadSummary])
async def list_leads(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    has_website: bool | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    sort_by: SortField = Query(default="created_at"),
    sort_order: SortOrder = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repo: LeadRepository = Depends(_repo),
):
    filters = LeadFilterParams(
        search=search,
        category=category,
        status=status_filter,  # type: ignore[arg-type]
        has_website=has_website,
        min_score=min_score,
        max_score=max_score,
        min_rating=min_rating,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    items, total = await repo.list(filters)
    return PaginatedResponse.build(
        items=[LeadSummary.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats/summary")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats across ALL leads (not paginated)."""
    total = (await db.execute(select(func.count()).select_from(Lead))).scalar_one()
    no_website = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.has_website == False)  # noqa: E712
    )).scalar_one()
    scored = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.ai_score.isnot(None))
    )).scalar_one()
    avg_score = (await db.execute(
        select(func.avg(Lead.ai_score)).where(Lead.ai_score.isnot(None))
    )).scalar_one()
    personalized = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.outreach_whatsapp.isnot(None))
    )).scalar_one()
    return {
        "total": total,
        "no_website": no_website,
        "scored": scored,
        "avg_score": round(avg_score) if avg_score else None,
        "personalized": personalized,
    }


@router.delete("/bulk", status_code=status.HTTP_200_OK)
async def bulk_delete_leads(
    ids: list[int] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete multiple leads by ID list."""
    result = await db.execute(delete(Lead).where(Lead.id.in_(ids)))
    await db.commit()
    return {"deleted": result.rowcount}


@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_leads(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete every lead in the database."""
    result = await db.execute(delete(Lead))
    await db.commit()
    return {"deleted": result.rowcount}


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: int,
    repo: LeadRepository = Depends(_repo),
):
    lead = await repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    repo: LeadRepository = Depends(_repo),
    _: str = Depends(verify_api_key),
):
    lead = await repo.update(lead_id, payload)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.patch("/{lead_id}/status", response_model=LeadRead)
async def update_lead_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    repo: LeadRepository = Depends(_repo),
    _: str = Depends(verify_api_key),
):
    lead = await repo.update_status(lead_id, payload.status)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    repo = LeadRepository(db)
    lead = await repo.get_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    await db.delete(lead)
