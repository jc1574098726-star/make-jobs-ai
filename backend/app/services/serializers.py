from __future__ import annotations

import json
from typing import Optional

from app.db import loads_json
from app.models import (
    ApplicationRecord,
    JobRecord,
    RecommendedJobRecord,
    ResumeProfileRecord,
    TailoredResumeRecord,
)
from app.schemas import (
    ApplicationView,
    InternshipEntry,
    JobView,
    ProjectEntry,
    CampusEntry,
    RecommendedJobView,
    ResumeProfileInput,
    ResumeProfileView,
    TailoredResumeView,
)


PLATFORM_LABELS = {
    "manual": "手动导入",
    "boss": "BOSS直聘",
    "zhaopin": "智联招聘",
    "51job": "前程无忧",
    "yingjiesheng": "应届生求职",
    "liepin": "猎聘",
    "linkedin": "LinkedIn",
}

AUTO_APPLY_PLATFORMS = {"boss", "zhaopin"}


def normalize_platform(platform: Optional[str]) -> str:
    if not platform:
        return "manual"
    normalized = platform.strip().lower()
    aliases = {
        "boss直聘": "boss",
        "boss": "boss",
        "zhipin": "boss",
        "智联": "zhaopin",
        "智联招聘": "zhaopin",
        "zhaopin": "zhaopin",
        "前程无忧": "51job",
        "51job": "51job",
        "yingjiesheng": "yingjiesheng",
        "应届生": "yingjiesheng",
        "应届生求职": "yingjiesheng",
        "liepin": "liepin",
        "猎聘": "liepin",
        "manual": "manual",
    }
    return aliases.get(normalized, normalized or "manual")


def platform_label(platform: str) -> str:
    return PLATFORM_LABELS.get(platform, platform)


def resume_record_to_view(record: ResumeProfileRecord) -> ResumeProfileView:
    profile_dict = loads_json(record.profile_json)
    return ResumeProfileView(
        id=record.id or 0,
        personal_info=profile_dict.get("personal_info") or {},
        self_evaluation=profile_dict.get("self_evaluation") or {},
        education_background=profile_dict.get("education_background") or [],
        internship_experiences=profile_dict.get("internship_experiences") or [],
        project_experiences=profile_dict.get("project_experiences") or [],
        campus_experiences=profile_dict.get("campus_experiences") or [],
        honors_and_certificates=profile_dict.get("honors_and_certificates") or [],
        training_experiences=profile_dict.get("training_experiences") or [],
        skills_and_other=profile_dict.get("skills_and_other") or {},
        updated_at=record.updated_at,
    )


def resume_input_to_record(record: ResumeProfileRecord, payload: ResumeProfileInput) -> ResumeProfileRecord:
    record.full_name = payload.personal_info.full_name or ""
    record.profile_json = json.dumps(payload.model_dump(), ensure_ascii=False)
    return record


def job_record_to_view(record: JobRecord) -> JobView:
    return JobView(
        id=record.id or 0,
        platform=record.platform,
        platform_label=platform_label(record.platform),
        source_url=record.source_url,
        raw_text=record.raw_text,
        job_title=record.job_title,
        company_name=record.company_name,
        city=record.city,
        salary_range=record.salary_range,
        experience_requirement=record.experience_requirement,
        education_requirement=record.education_requirement,
        skills=loads_json(record.skills_json),
        responsibilities=loads_json(record.responsibilities_json),
        highlights=loads_json(record.highlights_json),
        created_at=record.created_at,
    )


def tailored_resume_record_to_view(record: TailoredResumeRecord) -> TailoredResumeView:
    return TailoredResumeView(
        id=record.id or 0,
        job_id=record.job_id,
        resume_profile_id=record.resume_profile_id,
        match_score=record.match_score,
        professional_summary=record.professional_summary,
        selected_skills=loads_json(record.selected_skills_json),
        selected_internships=[InternshipEntry.model_validate(item) for item in loads_json(record.selected_experiences_json).get("internships", [])],
        selected_projects=[ProjectEntry.model_validate(item) for item in loads_json(record.selected_experiences_json).get("projects", [])],
        selected_campus=[CampusEntry.model_validate(item) for item in loads_json(record.selected_experiences_json).get("campus", [])],
        fit_strengths=loads_json(record.fit_strengths_json),
        fit_gaps=loads_json(record.fit_gaps_json),
        rendered_markdown=record.rendered_markdown,
        created_at=record.created_at,
    )


def application_record_to_view(record: ApplicationRecord) -> ApplicationView:
    return ApplicationView(
        id=record.id or 0,
        job_id=record.job_id,
        tailored_resume_id=record.tailored_resume_id,
        platform=record.platform,
        platform_label=platform_label(record.platform),
        status=record.status,
        auto_supported=record.auto_supported,
        target_url=record.target_url,
        notes=record.notes,
        created_at=record.created_at,
        confirmed_at=record.confirmed_at,
    )


def recommended_job_record_to_view(record: RecommendedJobRecord) -> RecommendedJobView:
    return RecommendedJobView(
        id=record.id or 0,
        platform=record.platform,
        platform_label=platform_label(record.platform),
        source_url=record.source_url,
        raw_text=record.raw_text,
        job_title=record.job_title,
        company_name=record.company_name,
        city=record.city,
        salary_range=record.salary_range,
        skills=loads_json(record.skills_json),
        highlights=loads_json(record.highlights_json),
        match_score=record.match_score,
        matched_skills=loads_json(record.matched_skills_json),
        missing_skills=loads_json(record.missing_skills_json),
        recommendation=record.recommendation,
        status=record.status,
        created_at=record.created_at,
        last_seen_at=record.last_seen_at,
    )
