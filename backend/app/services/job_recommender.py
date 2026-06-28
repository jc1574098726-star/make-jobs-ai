from __future__ import annotations

from typing import Dict, List, Optional

from app.schemas import MatchAnalysis, ResumeProfileView
from app.services.jd_parser import JobParserService
from app.services.matcher import MatcherService
from app.services.platform_search import PlatformSearchService
from app.services.serializers import normalize_platform


class JobRecommenderService:
    def __init__(self) -> None:
        self._search_service = PlatformSearchService()
        self._parser_service = JobParserService()
        self._matcher_service = MatcherService()

    def collect(self, profile: ResumeProfileView, preferences: Optional[Dict] = None) -> List[dict]:
        results = []
        parse_mode = (preferences or {}).get("parse_mode", "local")
        use_api = parse_mode == "api"
        for raw_item in self._search_service.search_jobs(profile, preferences):
            parsed = self._parser_service.parse(raw_item["raw_text"], use_api=use_api)
            analysis: MatchAnalysis = self._matcher_service.analyze(
                profile, parsed.skills, parsed.responsibilities,
                job_title=parsed.job_title or raw_item.get("job_title", ""),
                company_name=parsed.company_name or raw_item.get("company_name", ""),
                use_api=use_api,
            )
            results.append(
                {
                    "platform": normalize_platform(raw_item["platform"]),
                    "source_url": raw_item.get("source_url"),
                    "raw_text": raw_item["raw_text"],
                    "job_title": parsed.job_title or raw_item.get("job_title") or "未命名岗位",
                    "company_name": parsed.company_name or raw_item.get("company_name") or "待确认公司",
                    "city": parsed.city or raw_item.get("city"),
                    "salary_range": parsed.salary_range or raw_item.get("salary_range"),
                    "skills": parsed.skills,
                    "highlights": parsed.highlights,
                    "analysis": analysis,
                }
            )
        return sorted(results, key=lambda item: item["analysis"].match_score, reverse=True)
