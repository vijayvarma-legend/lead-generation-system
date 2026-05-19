"""Seed endpoint — inserts realistic sample leads for local testing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lead import Lead
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate

router = APIRouter(prefix="/leads", tags=["Leads"])

SAMPLE_LEADS: list[dict] = [
    {
        "business_name": "The Spice Garden Restaurant",
        "category": "Restaurant",
        "address": "12 MG Road, Bangalore, Karnataka 560001",
        "phone": "+91 80 2345 6789",
        "website": None,
        "rating": 4.1,
        "reviews_count": 87,
        "latitude": 12.9756,
        "longitude": 77.6097,
        "source_keyword": "restaurants",
    },
    {
        "business_name": "Glow & Shine Beauty Salon",
        "category": "Beauty Salon",
        "address": "45 Indiranagar, Bangalore, Karnataka 560038",
        "phone": "+91 98765 43210",
        "website": "http://glowshine.in",
        "rating": 3.8,
        "reviews_count": 34,
        "latitude": 12.9784,
        "longitude": 77.6408,
        "source_keyword": "salons",
    },
    {
        "business_name": "FitZone Gym & Fitness",
        "category": "Gym",
        "address": "78 Koramangala 5th Block, Bangalore 560095",
        "phone": "+91 91234 56789",
        "website": None,
        "rating": 4.5,
        "reviews_count": 210,
        "latitude": 12.9352,
        "longitude": 77.6245,
        "source_keyword": "gyms",
    },
    {
        "business_name": "Sunrise Dental Clinic",
        "category": "Dental Clinic",
        "address": "23 Jayanagar 4th Block, Bangalore 560041",
        "phone": "+91 80 4123 7890",
        "website": "https://sunrisedental.com",
        "rating": 4.7,
        "reviews_count": 512,
        "latitude": 12.9254,
        "longitude": 77.5832,
        "source_keyword": "dental clinics",
    },
    {
        "business_name": "Royal Sweets & Bakery",
        "category": "Bakery",
        "address": "5 Commercial Street, Bangalore 560001",
        "phone": "+91 80 2211 3344",
        "website": None,
        "rating": 4.3,
        "reviews_count": 19,
        "latitude": 12.9813,
        "longitude": 77.6088,
        "source_keyword": "bakeries",
    },
    {
        "business_name": "Tech Fix Mobile Repairs",
        "category": "Mobile Repair Shop",
        "address": "102 Brigade Road, Bangalore 560025",
        "phone": "+91 99887 76655",
        "website": None,
        "rating": 3.5,
        "reviews_count": 8,
        "latitude": 12.9716,
        "longitude": 77.6099,
        "source_keyword": "mobile repair",
    },
    {
        "business_name": "Green Leaf Yoga Studio",
        "category": "Yoga Studio",
        "address": "67 HSR Layout, Bangalore 560102",
        "phone": "+91 90123 45678",
        "website": "https://greenleafyoga.in",
        "rating": 4.9,
        "reviews_count": 143,
        "latitude": 12.9116,
        "longitude": 77.6389,
        "source_keyword": "yoga studios",
    },
    {
        "business_name": "Classic Car Service Center",
        "category": "Auto Repair",
        "address": "34 Electronic City Phase 1, Bangalore 560100",
        "phone": "+91 88901 23456",
        "website": None,
        "rating": 4.0,
        "reviews_count": 56,
        "latitude": 12.8399,
        "longitude": 77.6770,
        "source_keyword": "car service",
    },
    {
        "business_name": "Namma Tiffin Home Food",
        "category": "Tiffin Service",
        "address": "Whitefield Main Road, Bangalore 560066",
        "phone": "+91 77665 44332",
        "website": None,
        "rating": 4.6,
        "reviews_count": 5,
        "latitude": 12.9698,
        "longitude": 77.7499,
        "source_keyword": "tiffin services",
    },
    {
        "business_name": "Prestige Photo Studio",
        "category": "Photography Studio",
        "address": "88 Residency Road, Bangalore 560025",
        "phone": "+91 80 2299 4455",
        "website": "http://prestigephoto.com",
        "rating": 4.2,
        "reviews_count": 29,
        "latitude": 12.9678,
        "longitude": 77.6002,
        "source_keyword": "photo studios",
    },
]


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_sample_leads(db: AsyncSession = Depends(get_db)):
    """Insert 10 realistic sample Bangalore leads. Safe to call multiple times — skips duplicates."""
    repo = LeadRepository(db)
    created = []

    for data in SAMPLE_LEADS:
        result = await db.execute(
            select(Lead).where(Lead.business_name == data["business_name"])
        )
        if result.scalar_one_or_none():
            continue
        lead = await repo.create(LeadCreate(**data))
        created.append(lead.business_name)

    await db.commit()
    return {
        "message": f"Seeded {len(created)} new leads",
        "created": created,
        "skipped": len(SAMPLE_LEADS) - len(created),
    }
