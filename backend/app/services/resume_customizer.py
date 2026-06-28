from __future__ import annotations

from typing import Dict, List, Tuple

from app.schemas import (
    AIResumeSummary,
    JobView,
    MatchAnalysis,
    ResumeProfileView,
)
from app.services.claude_service import ClaudeService


class ResumeCustomizerService:
    def __init__(self) -> None:
        self._claude = ClaudeService._instance or ClaudeService()

    def build(
        self,
        profile: ResumeProfileView,
        job: JobView,
        analysis: MatchAnalysis,
    ) -> Tuple[str, List[str], List[Dict], List[Dict], List[Dict], List[str], List[str], str]:
        all_skills = profile.skills_and_other.skills
        selected_skills = self._select_skills(all_skills, analysis)
        selected_internships = self._select_internships(profile, analysis)
        selected_projects = self._select_projects(profile, analysis)
        selected_campus = self._select_campus(profile, analysis)
        selected_experiences_dicts = (
            [e.model_dump() for e in selected_internships]
            + [e.model_dump() for e in selected_projects]
            + [e.model_dump() for e in selected_campus]
        )
        ai_summary = self._build_ai_summary(profile, job, analysis, selected_skills, selected_experiences_dicts)
        markdown = self._render_markdown(
            profile,
            ai_summary.professional_summary,
            selected_skills,
            selected_internships,
            selected_projects,
            selected_campus,
            ai_summary.fit_strengths,
            ai_summary.fit_gaps,
        )
        return (
            ai_summary.professional_summary,
            selected_skills,
            selected_internships,
            selected_projects,
            selected_campus,
            ai_summary.fit_strengths,
            ai_summary.fit_gaps,
            markdown,
        )

    def _select_skills(self, profile_skills: List[str], analysis: MatchAnalysis) -> List[str]:
        priority = [skill for skill in analysis.matched_skills if skill in profile_skills]
        remaining = [skill for skill in profile_skills if skill not in priority]
        return (priority + remaining)[:8]

    def _select_internships(self, profile: ResumeProfileView, analysis: MatchAnalysis) -> List[dict]:
        keywords = {skill.lower() for skill in analysis.matched_skills}
        scored = []
        for item in profile.internship_experiences:
            score = self._score_experience(item, keywords)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:2]]

    def _select_projects(self, profile: ResumeProfileView, analysis: MatchAnalysis) -> List[dict]:
        keywords = {skill.lower() for skill in analysis.matched_skills}
        scored = []
        for item in profile.project_experiences:
            score = self._score_experience(item, keywords)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:2]]

    def _select_campus(self, profile: ResumeProfileView, analysis: MatchAnalysis) -> List[dict]:
        keywords = {skill.lower() for skill in analysis.matched_skills}
        scored = []
        for item in profile.campus_experiences:
            score = 0
            for highlight in item.highlights:
                if any(kw in highlight.lower() for kw in keywords):
                    score += 1
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:2]]

    def _score_experience(self, item, keywords: set) -> int:
        score = 0
        for skill in getattr(item, "skills", []):
            if skill.lower() in keywords:
                score += 2
        for highlight in getattr(item, "highlights", []):
            if any(kw in highlight.lower() for kw in keywords):
                score += 1
        return score

    def _build_ai_summary(
        self,
        profile: ResumeProfileView,
        job: JobView,
        analysis: MatchAnalysis,
        selected_skills: List[str],
        selected_experiences: List[Dict],
    ) -> AIResumeSummary:
        fallback = AIResumeSummary(
            professional_summary=self._build_summary(profile, analysis, selected_skills),
            fit_strengths=analysis.strengths,
            fit_gaps=analysis.gaps,
        )
        if not self._claude.enabled:
            return fallback
        try:
            return self._claude.summarize_resume(profile, job, analysis, selected_skills, selected_experiences)
        except Exception:
            return fallback

    def _build_summary(self, profile: ResumeProfileView, analysis: MatchAnalysis, selected_skills: List[str]) -> str:
        focus = "、".join(selected_skills[:4]) if selected_skills else ""
        name = profile.personal_info.full_name or "候选人"
        intention = profile.personal_info.job_intention or profile.self_evaluation.content
        total_experiences = (
            len(profile.internship_experiences)
            + len(profile.project_experiences)
            + len(profile.campus_experiences)
        )
        if focus:
            return "{}，具备 {} 段相关实践经历，围绕 {} 有可复用的真实项目经验，可快速贴合目标岗位的交付要求。".format(
                name or intention, total_experiences, focus
            )
        return "{}，具备 {} 段相关实践经历，可基于现有真实经历突出开发、自动化与数据处理能力。".format(
            name or intention, total_experiences
        )

    def _render_markdown(
        self,
        profile: ResumeProfileView,
        summary: str,
        selected_skills: List[str],
        selected_internships: list,
        selected_projects: list,
        selected_campus: list,
        fit_strengths: List[str],
        fit_gaps: List[str],
    ) -> str:
        sections = []  # type: List[str]
        name = profile.personal_info.full_name
        if name:
            sections.append("# {}".format(name))
            sections.append("")

        pi = profile.personal_info
        contact_parts = []
        if pi.job_intention:
            contact_parts.append("求职意向：{}".format(pi.job_intention))
        if pi.contact:
            contact_parts.append("电话：{}".format(pi.contact))
        if pi.email:
            contact_parts.append("邮箱：{}".format(pi.email))
        if pi.hometown:
            contact_parts.append("籍贯：{}".format(pi.hometown))
        if pi.birth_date:
            contact_parts.append("出生年月：{}".format(pi.birth_date))
        if pi.political_status:
            contact_parts.append("政治面貌：{}".format(pi.political_status))
        if contact_parts:
            sections.append("## 个人信息")
            sections.append(" | ".join(contact_parts))
            sections.append("")

        if summary:
            sections.append("## 自我评价")
            sections.append(summary)
            sections.append("")

        if profile.education_background:
            sections.append("## 教育背景")
            for edu in profile.education_background:
                parts = [edu.school_name, edu.attendance_period, edu.degree]
                sections.append("- {}".format(" | ".join(p for p in parts if p)))
                if edu.ranking:
                    sections.append("  排名：{}".format(edu.ranking))
                if edu.major_courses:
                    sections.append("  主修课程：{}".format(edu.major_courses))
            sections.append("")

        if selected_internships:
            sections.append("## 实习经历")
            for item in selected_internships:
                sections.append("### {} / {} ({})".format(item.company, item.role, item.duration))
                if item.summary:
                    sections.append(item.summary)
                for h in item.highlights:
                    sections.append("- {}".format(h))
                if item.skills:
                    sections.append("- 技能：{}".format("、".join(item.skills)))
                sections.append("")

        if selected_projects:
            sections.append("## 项目经历")
            for item in selected_projects:
                sections.append("### {} / {} ({})".format(item.project_name, item.role, item.duration))
                if item.summary:
                    sections.append(item.summary)
                for h in item.highlights:
                    sections.append("- {}".format(h))
                if item.skills:
                    sections.append("- 技能：{}".format("、".join(item.skills)))
                sections.append("")

        if selected_campus:
            sections.append("## 校园经历")
            for item in selected_campus:
                sections.append("### {} / {} ({})".format(item.organization, item.role, item.duration))
                if item.summary:
                    sections.append(item.summary)
                for h in item.highlights:
                    sections.append("- {}".format(h))
                sections.append("")

        if profile.honors_and_certificates:
            sections.append("## 荣誉证书")
            for honor in profile.honors_and_certificates:
                parts = [honor.name, honor.time, honor.issuer]
                sections.append("- {}".format(" | ".join(p for p in parts if p)))
            sections.append("")

        if profile.training_experiences:
            sections.append("## 培训经历")
            for training in profile.training_experiences:
                sections.append("### {} ({})".format(training.course_name, training.duration))
                if training.institution:
                    sections.append("培训机构：{}".format(training.institution))
                if training.summary:
                    sections.append(training.summary)
            sections.append("")

        if selected_skills:
            sections.append("## 技能及其他")
            sections.extend(["- {}".format(s) for s in selected_skills])
            if profile.skills_and_other.other:
                sections.append("")
                sections.append(profile.skills_and_other.other)
            sections.append("")

        if fit_strengths:
            sections.append("## 岗位匹配亮点")
            sections.extend(["- {}".format(s) for s in fit_strengths])
            sections.append("")

        if fit_gaps:
            sections.append("## 待补充说明")
            sections.extend(["- {}".format(g) for g in fit_gaps])

        return "\n".join(sections).strip()
