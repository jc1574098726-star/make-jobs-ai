"""Browser scraper dispatcher — delegates to platform-specific scrapers."""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class BrowserScraperService:
    def __init__(self, headed: bool = True):
        self._headed = headed

    def scrape_all_sync(
        self,
        platforms: List[str],
        keywords: List[str],
        cities: List[str],
        limit_per_search: int = 5,
    ) -> List[Dict]:
        import concurrent.futures

        def _run_in_new_loop():
            import sys
            if sys.platform == "win32":
                # Windows: use ProactorEventLoop for subprocess support
                try:
                    loop = asyncio.ProactorEventLoop()
                except Exception:
                    loop = asyncio.new_event_loop()
            else:
                loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._scrape_all(platforms, keywords, cities, limit_per_search)
                )
            finally:
                loop.close()

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return _run_in_new_loop()

        # FastAPI is running, use thread pool to avoid blocking
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_new_loop)
            return future.result(timeout=300)

    async def _scrape_all(
        self,
        platforms: List[str],
        keywords: List[str],
        cities: List[str],
        limit_per_search: int = 5,
    ) -> List[Dict]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed")
            return []

        from app.services.scrapers import SCRAPERS

        all_results: List[Dict] = []
        seen_urls: set = set()

        async with async_playwright() as pw:
            for platform_id in platforms:
                scraper_cls = SCRAPERS.get(platform_id)
                if not scraper_cls:
                    logger.warning("No scraper registered for platform: %s", platform_id)
                    continue

                scraper = scraper_cls(headed=self._headed)
                logger.info("Running scraper for %s", scraper.label)

                try:
                    results = await scraper.scrape(pw, keywords, cities, limit_per_search)
                    for job in results:
                        url = job.get("source_url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(job)
                except Exception as exc:
                    logger.warning("Scraper failed for %s: %s", platform_id, exc)

        return all_results
