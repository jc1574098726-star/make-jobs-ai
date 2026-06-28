from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.config import get_settings
from app.schemas import ResumeProfileView

logger = logging.getLogger(__name__)


class PlatformSearchService:
    def __init__(self) -> None:
        self._settings = get_settings()

    def search_jobs(self, profile: ResumeProfileView, preferences: Optional[Dict] = None) -> List[Dict]:
        limit = 10
        prefs = preferences or {}

        keywords = prefs.get("job_titles", [])[:3] or prefs.get("industry", [])[:3] or ["Python 开发工程师"]
        regions = prefs.get("regions", [])
        overseas = prefs.get("overseas", False)
        cities = regions[:3]
        if overseas:
            cities.append("海外")
        if not cities:
            cities = ["上海", "杭州", "深圳", "远程"]

        platforms = prefs.get("platforms", ["boss"])[:2]
        if not platforms:
            platforms = ["boss"]

        if self._settings.scrape_mode == "real":
            try:
                from app.services.browser_scraper import BrowserScraperService
                scraper = BrowserScraperService(headed=self._settings.browser_headed)
                real_results = scraper.scrape_all_sync(
                    platforms=platforms,
                    keywords=keywords,
                    cities=cities,
                    limit_per_search=max(3, limit // max(1, len(platforms))),
                )
                logger.info("Real scrape returned %d results", len(real_results))
                return real_results[:limit]
            except Exception as exc:
                import traceback
                logger.warning("Real scraping failed: %s\n%s", exc, traceback.format_exc())

        return []