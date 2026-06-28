from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional

from app.schemas import AIParsedJob
from app.services.claude_service import ClaudeService


KNOWN_SKILLS = {
    "python": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "sqlite": "SQLite",
    "react": "React",
    "vue": "Vue",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "playwright": "Playwright",
    "selenium": "Selenium",
    "automation": "Automation",
    "testing": "Testing",
    "data processing": "Data Processing",
    "llm": "LLM",
    "prompt engineering": "Prompt Engineering",
    "api": "API",
    "git": "Git",
}

CITY_NAMES = [
    "北京",
    "上海",
    "深圳",
    "广州",
    "杭州",
    "成都",
    "武汉",
    "苏州",
    "南京",
    "西安",
    "远程",
]


def _pick_first_match(patterns: List[str], raw_text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            value = next(group for group in match.groups() if group)
            return value.strip()
    return None


class JobParserService:
    def __init__(self) -> None:
        self._claude = ClaudeService._instance or ClaudeService()

    def parse(self, raw_text: str, use_api: bool = False) -> AIParsedJob:
        heuristic_result = self._parse_with_rules(raw_text)
        if not use_api or not self._claude.enabled:
            return heuristic_result
        try:
            return self._claude.parse_job(raw_text, heuristic_result)
        except Exception:
            return heuristic_result

    def _parse_with_rules(self, raw_text: str) -> AIParsedJob:
        cleaned = raw_text.strip()
        lines = [line.strip("-•● ") for line in cleaned.splitlines() if line.strip()]
        title = self._extract_title(lines, cleaned)
        company = self._extract_company(lines, cleaned)
        city = self._extract_city(cleaned)
        salary_range = self._extract_salary(cleaned)
        experience_requirement = self._extract_experience(cleaned)
        education_requirement = self._extract_education(cleaned)
        skills = self._extract_skills(cleaned)
        responsibilities = self._extract_responsibilities(lines)
        highlights = self._extract_highlights(cleaned, skills, salary_range)
        return AIParsedJob(
            job_title=title or "未命名岗位",
            company_name=company or "待确认公司",
            city=city,
            salary_range=salary_range,
            experience_requirement=experience_requirement,
            education_requirement=education_requirement,
            skills=skills,
            responsibilities=responsibilities,
            highlights=highlights,
        )

    def _extract_title(self, lines: List[str], raw_text: str) -> Optional[str]:
        for line in lines[:5]:
            if 2 <= len(line) <= 40 and not any(tag in line for tag in ["职责", "要求", "描述", "公司"]):
                return line
        return _pick_first_match([
            r"职位[名称岗位]*[:：]\s*([^\n]+)",
            r"招聘岗位[:：]\s*([^\n]+)",
        ], raw_text)

    def _extract_company(self, lines: List[str], raw_text: str) -> Optional[str]:
        patterns = [
            r"公司[名称]*[:：]\s*([^\n]+)",
            r"企业[名称]*[:：]\s*([^\n]+)",
        ]
        company = _pick_first_match(patterns, raw_text)
        if company:
            return company
        for line in lines[:8]:
            if any(token in line.lower() for token in ["有限公司", "科技", "信息", "网络", "studio", "tech", "公司"]):
                return line
        return None

    def _extract_city(self, raw_text: str) -> Optional[str]:
        for city in CITY_NAMES:
            if city in raw_text:
                return city
        return None

    def _extract_salary(self, raw_text: str) -> Optional[str]:
        match = re.search(r"(\d{1,3}(?:[-~—]\d{1,3})?[kK]|\d{4,6}(?:[-~—]\d{4,6})?元/月)", raw_text)
        return match.group(1) if match else None

    def _extract_experience(self, raw_text: str) -> Optional[str]:
        return _pick_first_match([
            r"(\d+[-+]?(?:年)?经验)",
            r"((?:应届|1-3年|3-5年|5年以上))",
        ], raw_text)

    def _extract_education(self, raw_text: str) -> Optional[str]:
        return _pick_first_match([
            r"(本科及以上|本科|大专及以上|大专|硕士及以上|硕士)",
        ], raw_text)

    def _extract_skills(self, raw_text: str) -> List[str]:
        text = raw_text.lower()
        matched = []
        for raw_skill, label in KNOWN_SKILLS.items():
            if raw_skill in text:
                matched.append(label)
        return list(dict.fromkeys(matched))

    def _extract_responsibilities(self, lines: List[str]) -> List[str]:
        collected: List[str] = []
        for line in lines:
            if len(collected) >= 6:
                break
            lowered = line.lower()
            if any(token in lowered for token in ["负责", "参与", "设计", "开发", "优化", "维护", "搭建", "编写"]):
                collected.append(line)
        return collected[:5]

    def _extract_highlights(self, raw_text: str, skills: List[str], salary_range: Optional[str]) -> List[str]:
        factors = Counter()
        if salary_range:
            factors["薪资信息明确"] += 1
        if len(skills) >= 4:
            factors["技能要求较完整"] += 1
        if "远程" in raw_text:
            factors["支持远程关键词"] += 1
        if "ai" in raw_text.lower() or "llm" in raw_text.lower():
            factors["包含 AI / LLM 方向"] += 1
        return list(factors.keys())
