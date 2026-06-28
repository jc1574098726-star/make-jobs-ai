from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Resume section models (all fields optional / defaultable)
# ---------------------------------------------------------------------------

class PersonalInfo(StrictBaseModel):
    full_name: str = ""
    job_intention: str = ""
    political_status: str = ""
    birth_date: str = ""
    hometown: str = ""
    contact: str = ""
    email: str = ""
    hobbies: str = ""
    strengths: str = ""


class SelfEvaluation(StrictBaseModel):
    content: str = ""


class EducationEntry(StrictBaseModel):
    school_name: str = ""
    attendance_period: str = ""
    degree: str = ""
    ranking: str = ""
    major_courses: str = ""


class InternshipEntry(StrictBaseModel):
    company: str = ""
    role: str = ""
    duration: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class ProjectEntry(StrictBaseModel):
    project_name: str = ""
    role: str = ""
    duration: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class CampusEntry(StrictBaseModel):
    organization: str = ""
    role: str = ""
    duration: str = ""
    summary: str = ""
    highlights: List[str] = Field(default_factory=list)


class HonorEntry(StrictBaseModel):
    name: str = ""
    time: str = ""
    issuer: str = ""


class TrainingEntry(StrictBaseModel):
    course_name: str = ""
    institution: str = ""
    duration: str = ""
    summary: str = ""


class SkillsAndOther(StrictBaseModel):
    skills: List[str] = Field(default_factory=list)
    other: str = ""


class ResumeProfileInput(StrictBaseModel):
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    self_evaluation: SelfEvaluation = Field(default_factory=SelfEvaluation)
    education_background: List[EducationEntry] = Field(default_factory=list)
    internship_experiences: List[InternshipEntry] = Field(default_factory=list)
    project_experiences: List[ProjectEntry] = Field(default_factory=list)
    campus_experiences: List[CampusEntry] = Field(default_factory=list)
    honors_and_certificates: List[HonorEntry] = Field(default_factory=list)
    training_experiences: List[TrainingEntry] = Field(default_factory=list)
    skills_and_other: SkillsAndOther = Field(default_factory=SkillsAndOther)


class ResumeProfileView(ResumeProfileInput):
    id: int
    updated_at: str


class ResumeUploadParseResponse(StrictBaseModel):
    file_name: str
    parsed_text_excerpt: str
    profile: ResumeProfileInput


# ---------------------------------------------------------------------------
# Job / application / recommendation models (unchanged)
# ---------------------------------------------------------------------------

class JobImportRequest(StrictBaseModel):
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    raw_text: str


class FetchUrlRequest(StrictBaseModel):
    url: str = ""
    raw_text: Optional[str] = None


class JobView(StrictBaseModel):
    id: int
    platform: str
    platform_label: str
    source_url: Optional[str] = None
    raw_text: str
    job_title: str
    company_name: str
    city: Optional[str] = None
    salary_range: Optional[str] = None
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    created_at: str


class MatchAnalysis(StrictBaseModel):
    match_score: int
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendation: str


class TailoredResumeView(StrictBaseModel):
    id: int
    job_id: int
    resume_profile_id: int
    match_score: int
    professional_summary: str
    selected_skills: List[str] = Field(default_factory=list)
    selected_internships: List[InternshipEntry] = Field(default_factory=list)
    selected_projects: List[ProjectEntry] = Field(default_factory=list)
    selected_campus: List[CampusEntry] = Field(default_factory=list)
    fit_strengths: List[str] = Field(default_factory=list)
    fit_gaps: List[str] = Field(default_factory=list)
    rendered_markdown: str
    created_at: str


class ApplicationView(StrictBaseModel):
    id: int
    job_id: int
    tailored_resume_id: int
    platform: str
    platform_label: str
    status: str
    auto_supported: bool
    target_url: Optional[str] = None
    notes: str
    created_at: str
    confirmed_at: Optional[str] = None


class RecommendedJobView(StrictBaseModel):
    id: int
    platform: str
    platform_label: str
    source_url: Optional[str] = None
    raw_text: str
    job_title: str
    company_name: str
    city: Optional[str] = None
    salary_range: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    match_score: int
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    recommendation: str
    status: str
    created_at: str
    last_seen_at: str


class PreparedApplicationResponse(StrictBaseModel):
    job: JobView
    analysis: MatchAnalysis
    tailored_resume: TailoredResumeView
    application: ApplicationView


class AIParsedJob(StrictBaseModel):
    job_title: str
    company_name: str
    city: Optional[str] = None
    salary_range: Optional[str] = None
    experience_requirement: Optional[str] = None
    education_requirement: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class AIResumeSummary(StrictBaseModel):
    professional_summary: str
    fit_strengths: List[str] = Field(default_factory=list)
    fit_gaps: List[str] = Field(default_factory=list)


class OverviewResponse(StrictBaseModel):
    profile: Optional[ResumeProfileView] = None
    jobs: List[JobView] = Field(default_factory=list)
    applications: List[ApplicationView] = Field(default_factory=list)
    recommended_jobs: List[RecommendedJobView] = Field(default_factory=list)
