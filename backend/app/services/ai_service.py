"""AI service — outreach generation and lead scoring via OpenAI."""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.prompts.outreach_prompts import (
    OUTREACH_SYSTEM_PROMPT,
    SCORING_SYSTEM_PROMPT,
    build_outreach_prompt,
    build_scoring_analysis_prompt,
)
from app.schemas.analysis import OutreachMessages, ScoreBreakdown, ScoreResult

logger = get_logger(__name__)


class AIService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

    async def generate_outreach(self, business: dict[str, Any]) -> OutreachMessages:
        """Generate email, WhatsApp, and DM outreach messages."""
        prompt = build_outreach_prompt(business)
        logger.info("Generating outreach messages", business=business.get("business_name"))

        raw = await self._chat(system=OUTREACH_SYSTEM_PROMPT, user=prompt)
        parsed = self._parse_json(raw)

        whatsapp = parsed.get("whatsapp", "")
        return OutreachMessages(
            email=whatsapp,
            whatsapp=whatsapp,
            dm=parsed.get("dm", ""),
            primary=whatsapp,
        )

    async def generate_score(self, business: dict[str, Any]) -> ScoreResult:
        """Generate AI lead score with breakdown."""
        prompt = build_scoring_analysis_prompt(business)
        logger.info("Generating lead score", business=business.get("business_name"))

        raw = await self._chat(system=SCORING_SYSTEM_PROMPT, user=prompt)
        parsed = self._parse_json(raw)

        breakdown_data = parsed.get("breakdown", {})
        breakdown = ScoreBreakdown(
            website_existence=breakdown_data.get("website_existence", 0),
            website_quality=breakdown_data.get("website_quality", 0),
            reviews_and_rating=breakdown_data.get("reviews_and_rating", 0),
            social_presence=breakdown_data.get("social_presence", 0),
            mobile_optimization=breakdown_data.get("mobile_optimization", 0),
            total=breakdown_data.get("total", 0),
            reasoning=breakdown_data.get("reasoning", ""),
        )

        return ScoreResult(
            ai_score=parsed.get("ai_score", 0),
            breakdown=breakdown,
            recommendation=parsed.get("recommendation", ""),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _chat(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            # response_format not used — not supported by all OpenRouter models
        )
        content = response.choices[0].message.content or "{}"
        logger.debug(
            "OpenAI response received",
            tokens_used=response.usage.total_tokens if response.usage else None,
        )
        return content

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Best-effort: extract JSON block from fenced markdown
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            logger.warning("Failed to parse OpenAI JSON response", raw=raw[:200])
            return {}
