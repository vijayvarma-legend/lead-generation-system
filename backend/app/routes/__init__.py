from fastapi import APIRouter

from app.routes.analysis import router as analysis_router
from app.routes.health import router as health_router
from app.routes.leads import router as leads_router
from app.routes.personalization import router as personalization_router
from app.routes.scoring import router as scoring_router
from app.routes.seed import router as seed_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(leads_router)
api_router.include_router(seed_router)
api_router.include_router(analysis_router)
api_router.include_router(scoring_router)
api_router.include_router(personalization_router)

__all__ = ["api_router"]
