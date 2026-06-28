from __future__ import annotations

import re
from typing import List

from app.schemas import (
    EducationEntry,
    ProjectEntry,
    ResumeProfileInput,
    SkillsAndOther,
)


def infer_resume_profile_from_text(raw_text: str) -> ResumeProfileInput:
    lines = [line.strip("-•● ") for line in raw_text.splitlines() if line.strip()]
    lower_text = raw_text.lower()

    full_name = lines[0] if lines else ""
    job_intention = _extract_job_intention(lines)
    contact = _extract_contact(raw_text)
    email = _extract_email(raw_text)
    education = _extract_education(lines)
    skills = _extract_skills(lower_text)
    experiences = _extract_experiences(lines, skills)

    return ResumeProfileInput(
        personal_info={
            "full_name": full_name,
            "job_intention": job_intention,
            "political_status": "",
            "birth_date": "",
            "hometown": "",
            "contact": contact,
            "email": email,
            "hobbies": "",
            "strengths": "",
        },
        self_evaluation={"content": ""},
        education_background=education,
        internship_experiences=[],
        project_experiences=experiences,
        campus_experiences=[],
        honors_and_certificates=[],
        training_experiences=[],
        skills_and_other=SkillsAndOther(skills=skills, other=""),
    )


def _extract_job_intention(lines: List[str]) -> str:
    for line in lines[:10]:
        if any(token in line for token in ["工程师", "开发", "测试", "产品", "算法", "运营", "求职意向", "期望岗位"]):
            return line[:40]
    return ""


def _extract_contact(text: str) -> str:
    match = re.search(r"1[3-9]\d{9}", text)
    return match.group(0) if match else ""


def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def _extract_education(lines: List[str]) -> List[EducationEntry]:
    entries = []  # type: List[EducationEntry]
    for idx, line in enumerate(lines):
        if any(token in line for token in ["大学", "学院", "学校", "大专", "本科", "硕士", "博士"]):
            period = _pick_duration(line) or ""
            if not period and idx + 1 < len(lines):
                period = _pick_duration(lines[idx + 1]) or ""
            entries.append(EducationEntry(
                school_name=line[:40],
                attendance_period=period,
                degree="",
                ranking="",
                major_courses="",
            ))
            if len(entries) >= 2:
                break
    return entries


def _extract_skills(text: str) -> List[str]:
    skills_map = {
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
        "llm": "LLM",
        "ai": "AI",
        "prompt": "Prompt Engineering",
        "git": "Git",
        "docker": "Docker",
    }
    matched = []
    for raw, label in skills_map.items():
        if raw in text:
            matched.append(label)
    if matched:
        return list(dict.fromkeys(matched))[:12]
    return ["Python", "SQL"] if "python" in text else []


def _extract_experiences(lines: List[str], skills: List[str]) -> List[ProjectEntry]:
    experiences = []  # type: List[ProjectEntry]
    for idx, line in enumerate(lines):
        if len(experiences) >= 3:
            break
        if any(token in line for token in ["有限公司", "科技", "项目", "实习", "公司", "校园"]):
            role = lines[idx + 1] if idx + 1 < len(lines) else "经历待补充"
            duration = _pick_duration(line) or _pick_duration(role) or "时间待补充"
            summary = lines[idx + 2] if idx + 2 < len(lines) else "简历原文提到的相关经历。"
            highlights = []
            for follow in lines[idx + 2: idx + 5]:
                if follow != summary and len(highlights) < 3:
                    highlights.append(follow)
            experiences.append(ProjectEntry(
                project_name=line[:40],
                role=role[:40],
                duration=duration,
                summary=summary[:120],
                skills=skills[:4],
                highlights=highlights,
            ))
    return experiences


def _pick_duration(text: str) -> str:
    match = re.search(r"(20\d{2}[./-]?(?:20\d{2}|至今)?|\d{4}[-~—]\d{4}|\d+年)", text)
    return match.group(1) if match else ""
