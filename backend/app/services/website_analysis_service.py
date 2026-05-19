"""Website analysis service using Playwright."""

from __future__ import annotations

import re
from typing import Any

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.analysis import WebsiteAnalysisResult

logger = get_logger(__name__)

SOCIAL_PATTERNS = {
    "instagram": re.compile(r"instagram\.com/([^/?\"'\s]+)", re.I),
    "facebook": re.compile(r"facebook\.com/([^/?\"'\s]+)", re.I),
    "twitter": re.compile(r"twitter\.com/([^/?\"'\s]+)", re.I),
    "linkedin": re.compile(r"linkedin\.com/(?:company|in)/([^/?\"'\s]+)", re.I),
    "youtube": re.compile(r"youtube\.com/(?:channel|c|user)/([^/?\"'\s]+)", re.I),
    "whatsapp": re.compile(r"wa\.me/(\d+)", re.I),
}


class WebsiteAnalysisService:
    async def analyse(self, url: str) -> WebsiteAnalysisResult:
        """Launch Playwright, visit the URL, and extract signals."""
        logger.info("Starting website analysis", url=url)

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                page = await context.new_page()

                try:
                    await page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)  # let JS settle
                except PlaywrightTimeout:
                    logger.warning("Page load timed out", url=url)
                    await browser.close()
                    return WebsiteAnalysisResult(error="Page load timed out")

                html = await page.content()
                title = await page.title()
                text_content = await page.evaluate("() => document.body?.innerText || ''")

                headings = await self._extract_headings(page)
                social_links = self._extract_social_links(html)
                has_contact_form = await self._detect_contact_form(page)
                has_gallery = await self._detect_gallery(page)
                is_mobile_responsive = await self._check_mobile_responsive(context, url)
                has_modern_ui = self._detect_modern_ui(html)

                await browser.close()

        except Exception as exc:
            logger.error("Website analysis failed", url=url, error=str(exc))
            return WebsiteAnalysisResult(error=str(exc))

        quality_score, quality_label = self._compute_quality_score(
            has_contact_form=has_contact_form,
            has_gallery=has_gallery,
            is_mobile_responsive=is_mobile_responsive,
            has_modern_ui=has_modern_ui,
            social_links=social_links,
            headings=headings,
        )

        summary = self._build_summary(
            title=title,
            has_contact_form=has_contact_form,
            has_gallery=has_gallery,
            is_mobile_responsive=is_mobile_responsive,
            has_modern_ui=has_modern_ui,
            social_links=social_links,
            quality_score=quality_score,
        )

        result = WebsiteAnalysisResult(
            title=title,
            headings=headings[:10],
            social_links=social_links,
            has_contact_form=has_contact_form,
            has_gallery=has_gallery,
            is_mobile_responsive=is_mobile_responsive,
            has_modern_ui=has_modern_ui,
            website_quality_score=quality_score,
            website_quality=quality_label,
            analysis_summary=summary,
            raw_text_snippet=text_content[:500],
        )

        logger.info(
            "Website analysis complete",
            url=url,
            quality_score=quality_score,
            mobile=is_mobile_responsive,
        )
        return result

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    async def _extract_headings(self, page: Any) -> list[str]:
        headings = await page.evaluate("""
            () => Array.from(document.querySelectorAll('h1, h2, h3'))
                       .map(el => el.innerText.trim())
                       .filter(t => t.length > 0 && t.length < 200)
        """)
        return headings or []

    def _extract_social_links(self, html: str) -> dict[str, str]:
        found: dict[str, str] = {}
        for platform, pattern in SOCIAL_PATTERNS.items():
            match = pattern.search(html)
            if match:
                found[platform] = match.group(0)
        return found

    async def _detect_contact_form(self, page: Any) -> bool:
        try:
            forms = await page.query_selector_all("form")
            for form in forms:
                inputs = await form.query_selector_all("input, textarea")
                if len(inputs) >= 2:
                    return True
            # Also look for common contact page links
            contact_links = await page.query_selector_all("a[href*='contact'], a[href*='kontakt']")
            return len(contact_links) > 0
        except Exception:
            return False

    async def _detect_gallery(self, page: Any) -> bool:
        try:
            selectors = [
                ".gallery", "#gallery", "[class*='gallery']",
                "[class*='portfolio']", "[class*='slider']",
                ".swiper", ".carousel", "figure img",
            ]
            for sel in selectors:
                els = await page.query_selector_all(sel)
                if els:
                    return True
            # Heuristic: many images clustered together
            imgs = await page.query_selector_all("img")
            return len(imgs) >= 6
        except Exception:
            return False

    async def _check_mobile_responsive(self, context: Any, url: str) -> bool:
        try:
            mobile_page = await context.new_page()
            await mobile_page.set_viewport_size({"width": 390, "height": 844})
            await mobile_page.goto(url, timeout=settings.PLAYWRIGHT_TIMEOUT, wait_until="domcontentloaded")
            await mobile_page.wait_for_timeout(1000)

            # Check for meta viewport
            has_viewport = await mobile_page.evaluate("""
                () => !!document.querySelector('meta[name="viewport"]')
            """)
            # Check horizontal scroll (sign of non-responsive design)
            scroll_width = await mobile_page.evaluate("() => document.body.scrollWidth")
            client_width = await mobile_page.evaluate("() => document.documentElement.clientWidth")

            await mobile_page.close()
            return has_viewport and scroll_width <= client_width + 20
        except Exception:
            return False

    def _detect_modern_ui(self, html: str) -> bool:
        modern_signals = [
            "tailwind", "bootstrap", "material", "chakra", "ant-design",
            "react", "vue", "angular", "next", "nuxt",
            "flex", "grid", "css-modules", "styled-components",
        ]
        html_lower = html.lower()
        hits = sum(1 for s in modern_signals if s in html_lower)
        return hits >= 2

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _compute_quality_score(
        self,
        has_contact_form: bool,
        has_gallery: bool,
        is_mobile_responsive: bool,
        has_modern_ui: bool,
        social_links: dict,
        headings: list,
    ) -> tuple[int, str]:
        score = 0
        score += 30 if is_mobile_responsive else 0
        score += 25 if has_modern_ui else 0
        score += 20 if has_contact_form else 0
        score += 15 if has_gallery else 0
        score += min(len(social_links) * 5, 10)

        label = (
            "excellent" if score >= 80
            else "good" if score >= 60
            else "average" if score >= 40
            else "poor"
        )
        return score, label

    def _build_summary(self, **kwargs: Any) -> str:
        parts = [f"Title: {kwargs['title'] or 'N/A'}"]
        parts.append(f"Mobile responsive: {'Yes' if kwargs['is_mobile_responsive'] else 'No'}")
        parts.append(f"Modern UI: {'Yes' if kwargs['has_modern_ui'] else 'No'}")
        parts.append(f"Contact form: {'Yes' if kwargs['has_contact_form'] else 'No'}")
        parts.append(f"Gallery/portfolio: {'Yes' if kwargs['has_gallery'] else 'No'}")
        socials = list(kwargs["social_links"].keys())
        parts.append(f"Social links found: {', '.join(socials) if socials else 'None'}")
        parts.append(f"Quality score: {kwargs['quality_score']}/100")
        return " | ".join(parts)
