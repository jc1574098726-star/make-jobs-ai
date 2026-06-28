from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


class ResumeProfileRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = ""
    profile_json: str = "{}"
    updated_at: str


class JobRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str
    source_url: Optional[str] = None
    raw_text: str
    job_title: str
    company_name: str
    city: Optional[str] = None
    salary_range: Optional[str] = None
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    skills_json: str = "[]"
    responsibilities_json: str = "[]"
    highlights_json: str = "[]"
    created_at: str


class TailoredResumeRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int
    resume_profile_id: int
    match_score: int
    professional_summary: str
    selected_skills_json: str = "[]"
    selected_experiences_json: str = "[]"
    fit_strengths_json: str = "[]"
    fit_gaps_json: str = "[]"
    rendered_markdown: str
    created_at: str


class ApplicationRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int
    tailored_resume_id: int
    platform: str
    status: str
    auto_supported: bool = False
    target_url: Optional[str] = None
    notes: str = ""
    created_at: str
    confirmed_at: Optional[str] = None


class RecommendedJobRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str
    source_url: Optional[str] = None
    raw_text: str
    job_title: str
    company_name: str
    city: Optional[str] = None
    salary_range: Optional[str] = None
    skills_json: str = "[]"
    highlights_json: str = "[]"
    match_score: int = 0
    matched_skills_json: str = "[]"
    missing_skills_json: str = "[]"
    recommendation: str = ""
    status: str = "new"
    created_at: str
    last_seen_at: str
