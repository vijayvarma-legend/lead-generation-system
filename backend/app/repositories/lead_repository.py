"""Data-access layer for Lead entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import asc, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadFilterParams, LeadUpdate


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, lead_id: int) -> Lead | None:
        result = await self._session.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def get_by_place_id(self, place_id: str) -> Lead | None:
        result = await self._session.execute(
            select(Lead).where(Lead.place_id == place_id)
        )
        return result.scalar_one_or_none()

    async def list(self, filters: LeadFilterParams) -> tuple[list[Lead], int]:
        base_q = select(Lead)
        count_q = select(func.count()).select_from(Lead)

        # Filtering
        conditions = self._build_conditions(filters)
        if conditions:
            base_q = base_q.where(*conditions)
            count_q = count_q.where(*conditions)

        # Total count
        total_result = await self._session.execute(count_q)
        total = total_result.scalar_one()

        # Sorting
        sort_col = getattr(Lead, filters.sort_by, Lead.created_at)
        order_fn = asc if filters.sort_order == "asc" else desc
        base_q = base_q.order_by(order_fn(sort_col))

        # Pagination
        base_q = base_q.offset(filters.offset).limit(filters.page_size)

        result = await self._session.execute(base_q)
        return list(result.scalars().all()), total

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, data: LeadCreate) -> Lead:
        lead = Lead(
            **data.model_dump(exclude_none=False),
            has_website=bool(data.website),
        )
        self._session.add(lead)
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def update(self, lead_id: int, data: LeadUpdate) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if not lead:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(lead, field, value)
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def update_status(self, lead_id: int, status: LeadStatus) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if not lead:
            return None
        lead.status = status
        await self._session.flush()
        return lead

    async def save_analysis(self, lead_id: int, analysis: dict[str, Any]) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if not lead:
            return None
        for field, value in analysis.items():
            if hasattr(lead, field):
                setattr(lead, field, value)
        lead.analyzed_at = datetime.now(timezone.utc)
        lead.status = LeadStatus.ANALYZED
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def save_score(self, lead_id: int, score_data: dict[str, Any]) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if not lead:
            return None
        lead.ai_score = score_data.get("ai_score")
        lead.score_breakdown = score_data.get("score_breakdown")
        lead.scored_at = datetime.now(timezone.utc)
        lead.status = LeadStatus.SCORED
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def save_outreach(self, lead_id: int, messages: dict[str, str]) -> Lead | None:
        lead = await self.get_by_id(lead_id)
        if not lead:
            return None
        lead.outreach_email = messages.get("email")
        lead.outreach_whatsapp = messages.get("whatsapp")
        lead.outreach_dm = messages.get("dm")
        lead.outreach_message = messages.get("email")  # primary
        lead.personalized_at = datetime.now(timezone.utc)
        lead.status = LeadStatus.PERSONALIZED
        await self._session.flush()
        await self._session.refresh(lead)
        return lead

    async def bulk_create(self, leads_data: list[LeadCreate]) -> list[Lead]:
        leads: list[Lead] = []
        for data in leads_data:
            existing = None
            if data.place_id:
                existing = await self.get_by_place_id(data.place_id)
            if not existing:
                leads.append(await self.create(data))
        return leads

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_conditions(self, filters: LeadFilterParams) -> list[Any]:
        conditions: list[Any] = []

        if filters.search:
            term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Lead.business_name.ilike(term),
                    Lead.address.ilike(term),
                    Lead.category.ilike(term),
                )
            )

        if filters.category:
            conditions.append(Lead.category.ilike(f"%{filters.category}%"))

        if filters.status:
            conditions.append(Lead.status == filters.status)

        if filters.has_website is not None:
            conditions.append(Lead.has_website == filters.has_website)

        if filters.min_score is not None:
            conditions.append(Lead.ai_score >= filters.min_score)

        if filters.max_score is not None:
            conditions.append(Lead.ai_score <= filters.max_score)

        if filters.min_rating is not None:
            conditions.append(Lead.rating >= filters.min_rating)

        return conditions
