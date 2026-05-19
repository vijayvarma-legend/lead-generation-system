"""Service for collecting business leads via Apify Google Maps scraper."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.lead import LeadCreate

logger = get_logger(__name__)

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_RUN_TIMEOUT = 300  # seconds


class LeadCollectionService:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=60.0)

    async def collect(
        self,
        keyword: str,
        latitude: float,
        longitude: float,
        radius: int,
        max_results: int = 20,
    ) -> list[LeadCreate]:
        """Run Apify actor and return normalised LeadCreate objects."""
        logger.info(
            "Starting lead collection",
            keyword=keyword,
            lat=latitude,
            lng=longitude,
            radius=radius,
        )

        try:
            run_id = await self._start_actor_run(keyword, latitude, longitude, radius, max_results)
            raw_items = await self._poll_and_fetch(run_id)
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            body = exc.response.text[:300]
            logger.error("Apify API error", status_code=status_code, body=body)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Apify API returned {status_code}. Check your APIFY_API_TOKEN and APIFY_GOOGLE_MAPS_ACTOR_ID. Details: {body}",
            )
        except (TimeoutError, RuntimeError) as exc:
            logger.error("Apify run failed", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(exc),
            )

        leads = [self._normalise(item, keyword, latitude, longitude, radius) for item in raw_items]
        logger.info("Lead collection finished", total=len(leads))
        return leads

    # ------------------------------------------------------------------
    # Apify interaction
    # ------------------------------------------------------------------

    async def _start_actor_run(
        self,
        keyword: str,
        lat: float,
        lng: float,
        radius: int,
        max_results: int,
    ) -> str:
        # Use username~actorname slug — required by Apify v2 API
        actor_id = settings.APIFY_GOOGLE_MAPS_ACTOR_ID
        url = f"{APIFY_BASE_URL}/acts/{actor_id}/runs?token={settings.APIFY_API_TOKEN}"

        # compass/crawler-google-places input schema
        payload = {
            "searchStringsArray": [keyword],
            "lat": lat,
            "lng": lng,
            "zoom": 14,
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "maxImages": 0,
            "includeWebResults": False,
            "scrapeDirectories": False,
            "deeperCityScrape": False,
        }

        logger.debug("Calling Apify actor", actor_id=actor_id, url=url)
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        run_id: str = data["data"]["id"]
        logger.debug("Apify actor run started", run_id=run_id)
        return run_id

    async def _poll_and_fetch(self, run_id: str) -> list[dict[str, Any]]:
        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}?token={settings.APIFY_API_TOKEN}"
        elapsed = 0
        poll_interval = 5

        while elapsed < ACTOR_RUN_TIMEOUT:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            resp = await self._client.get(status_url)
            resp.raise_for_status()
            run_data = resp.json()["data"]
            run_status = run_data.get("status")

            logger.debug("Apify run status", run_id=run_id, status=run_status, elapsed=elapsed)

            if run_status == "SUCCEEDED":
                dataset_id = run_data["defaultDatasetId"]
                return await self._fetch_dataset(dataset_id)
            elif run_status in ("FAILED", "ABORTED", "TIMED-OUT"):
                raise RuntimeError(f"Apify run {run_id} ended with status: {run_status}")

        raise TimeoutError(f"Apify run {run_id} did not complete within {ACTOR_RUN_TIMEOUT}s")

    async def _fetch_dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        url = (
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
            f"?token={settings.APIFY_API_TOKEN}&format=json&clean=true"
        )
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalise(
        self,
        item: dict[str, Any],
        keyword: str,
        src_lat: float,
        src_lng: float,
        radius: int,
    ) -> LeadCreate:
        website = item.get("website") or None
        social = item.get("socialMedia") or {}

        location = item.get("location") or {}
        lat = location.get("lat") or item.get("lat")
        lng = location.get("lng") or item.get("lng")

        return LeadCreate(
            business_name=item.get("title") or item.get("name") or "Unknown",
            category=self._extract_category(item),
            address=item.get("address") or item.get("street"),
            phone=item.get("phone") or item.get("phoneUnformatted"),
            email=item.get("email"),
            website=website,
            instagram=social.get("instagram"),
            facebook=social.get("facebook"),
            google_maps_url=item.get("url") or item.get("link"),
            place_id=item.get("placeId") or item.get("id"),
            rating=self._safe_float(item.get("totalScore") or item.get("rating")),
            reviews_count=self._safe_int(item.get("reviewsCount") or item.get("userRatingsTotal")),
            latitude=self._safe_float(lat),
            longitude=self._safe_float(lng),
            source_keyword=keyword,
            source_latitude=src_lat,
            source_longitude=src_lng,
            source_radius=radius,
        )

    @staticmethod
    def _extract_category(item: dict[str, Any]) -> str | None:
        cats = item.get("categories") or item.get("categoryName")
        if isinstance(cats, list) and cats:
            return cats[0]
        if isinstance(cats, str):
            return cats
        return item.get("type")

    @staticmethod
    def _safe_float(v: Any) -> float | None:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(v: Any) -> int | None:
        try:
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    async def aclose(self) -> None:
        await self._client.aclose()
