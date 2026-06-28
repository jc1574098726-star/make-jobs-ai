from __future__ import annotations

import logging
from typing import List

from app.schemas import MatchAnalysis, ResumeProfileView

logger = logging.getLogger(__name__)


class MatcherService:
    def analyze(
        self,
        profile: ResumeProfileView,
        job_skills: List[str],
        responsibilities: List[str],
        job_title: str = "",
        company_name: str = "",
        use_api: bool = False,
    ) -> MatchAnalysis:
        # 优先使用 Claude API
        from app.services.claude_service import ClaudeService

        claude = ClaudeService._instance
        if use_api and claude and claude.enabled:
            try:
                return claude.analyze_match(
                    profile, job_skills, responsibilities,
                    job_title=job_title, company_name=company_name,
                )
            except Exception as exc:
                logger.warning("Claude API match analysis failed, falling back to heuristic: %s", exc)

        # Fallback：启发式评分
        return self._analyze_heuristic(profile, job_skills, responsibilities)

    def _analyze_heuristic(self, profile: ResumeProfileView, job_skills: List[str], responsibilities: List[str]) -> MatchAnalysis:
        profile_skills = profile.skills_and_other.skills
        normalized_profile_skills = {skill.strip().lower() for skill in profile_skills}
        normalized_job_skills = [skill.strip().lower() for skill in job_skills if skill.strip()]

        matched = [skill for skill in job_skills if skill.strip().lower() in normalized_profile_skills]
        missing = [skill for skill in job_skills if skill.strip().lower() not in normalized_profile_skills]

        total_experiences = (
            len(profile.internship_experiences)
            + len(profile.project_experiences)
            + len(profile.campus_experiences)
        )
        score = self._score(total_experiences, matched, missing, responsibilities)
        strengths = self._build_strengths(profile, total_experiences, matched, responsibilities)
        gaps = self._build_gaps(missing)
        recommendation = self._build_recommendation(score, matched, missing)

        return MatchAnalysis(
            match_score=score,
            matched_skills=matched,
            missing_skills=missing,
            strengths=strengths,
            gaps=gaps,
            recommendation=recommendation,
        )

    def _score(
        self,
        total_experiences: int,
        matched: List[str],
        missing: List[str],
        responsibilities: List[str],
    ) -> int:
        base = 35
        base += min(len(matched) * 10, 40)
        base -= min(len(missing) * 4, 20)
        if total_experiences >= 2:
            base += 8
        if responsibilities:
            base += min(len(responsibilities) * 2, 10)
        return max(0, min(base, 100))

    def _build_strengths(
        self,
        profile: ResumeProfileView,
        total_experiences: int,
        matched: List[str],
        responsibilities: List[str],
    ) -> List[str]:
        strengths = []  # type: List[str]
        if matched:
            strengths.append("已覆盖岗位要求中的核心技能：{}".format("、".join(matched[:5])))
        if total_experiences > 0:
            strengths.append("已有 {} 段可重排的真实经历，可用于针对岗位突出重点。".format(total_experiences))
        if responsibilities:
            strengths.append("岗位职责描述清晰，便于按职责重组简历内容。")
        return strengths[:3]

    def _build_gaps(self, missing: List[str]) -> List[str]:
        if not missing:
            return ["技能层面没有明显缺口，可直接进入简历定制。"]
        return ["岗位提及但简历资料未明确覆盖：{}".format("、".join(missing[:5]))]

    def _build_recommendation(self, score: int, matched: List[str], missing: List[str]) -> str:
        if score >= 75:
            return "匹配度较高，建议优先生成定制简历并进入投递确认。"
        if matched and len(missing) <= max(1, len(matched)):
            return "具备一定匹配基础，建议突出命中技能并在摘要中弱化缺口。"
        return "匹配度一般，建议先补充相关项目或将其放入观察池。"
