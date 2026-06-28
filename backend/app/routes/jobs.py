from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db import dumps_json, get_session, utc_now
from app.models import ApplicationRecord, JobRecord, ResumeProfileRecord, TailoredResumeRecord
from app.schemas import FetchUrlRequest, JobImportRequest, JobView, MatchAnalysis, PreparedApplicationResponse, TailoredResumeView
from app.services.jd_parser import JobParserService
from app.services.matcher import MatcherService
from app.services.features.import_jobs import import_from_url
from app.services.resume_customizer import ResumeCustomizerService
from app.services.serializers import (
    AUTO_APPLY_PLATFORMS,
    application_record_to_view,
    job_record_to_view,
    normalize_platform,
    resume_record_to_view,
    tailored_resume_record_to_view,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
parser_service = JobParserService()
matcher_service = MatcherService()
customizer_service = ResumeCustomizerService()


@router.get("", response_model=List[JobView])
def list_jobs(session: Session = Depends(get_session)) -> List[JobView]:
    records = session.exec(select(JobRecord).order_by(desc(JobRecord.id))).all()
    return [job_record_to_view(record) for record in records]


@router.post("/import", response_model=JobView)
def import_job(payload: JobImportRequest, session: Session = Depends(get_session)) -> JobView:
    parsed = parser_service.parse(payload.raw_text)
    record = JobRecord(
        platform=normalize_platform(payload.source_platform),
        source_url=payload.source_url,
        raw_text=payload.raw_text,
        job_title=parsed.job_title,
        company_name=parsed.company_name,
        city=parsed.city,
        salary_range=parsed.salary_range,
        experience_requirement=parsed.experience_requirement,
        education_requirement=parsed.education_requirement,
        skills_json=dumps_json(parsed.skills),
        responsibilities_json=dumps_json(parsed.responsibilities),
        highlights_json=dumps_json(parsed.highlights),
        created_at=utc_now(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return job_record_to_view(record)


@router.post("/fetch-url")
def fetch_url(payload: FetchUrlRequest) -> dict:
    """根据 URL 抓取页面文本内容，或直接解析 raw_text，提取结构化字段。"""
    if payload.raw_text:
        from app.services.url_fetcher import extract_job_fields_with_ai
        fields = extract_job_fields_with_ai(payload.raw_text)
        return {"raw_text": payload.raw_text, **fields}
    if payload.url:
        return import_from_url(payload.url)
    return {"raw_text": "", "error": "请提供链接或岗位内容"}


@router.post("/clear")
def clear_jobs(session: Session = Depends(get_session)):
    records = session.exec(select(JobRecord)).all()
    for record in records:
        session.delete(record)
    session.commit()
    return {"ok": True}


@router.get("/{job_id}", response_model=JobView)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobView:
    record = session.get(JobRecord, job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_record_to_view(record)


@router.post("/{job_id}/prepare", response_model=PreparedApplicationResponse)
def prepare_application(job_id: int, match_mode: str = "local", session: Session = Depends(get_session)) -> PreparedApplicationResponse:
    job = session.get(JobRecord, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_record = session.exec(select(ResumeProfileRecord).order_by(desc(ResumeProfileRecord.id))).first()
    if not profile_record:
        raise HTTPException(status_code=400, detail="Resume profile is required before preparing applications")

    profile = resume_record_to_view(profile_record)
    job_view = job_record_to_view(job)
    analysis: MatchAnalysis = matcher_service.analyze(
        profile, job_view.skills, job_view.responsibilities,
        job_title=job_view.job_title, company_name=job_view.company_name,
        use_api=(match_mode == "ai"),
    )

    (
        summary,
        selected_skills,
        selected_internships,
        selected_projects,
        selected_campus,
        fit_strengths,
        fit_gaps,
        markdown,
    ) = customizer_service.build(profile, job_view, analysis)

    selected_experiences_dict = {
        "internships": [e.model_dump() for e in selected_internships],
        "projects": [e.model_dump() for e in selected_projects],
        "campus": [e.model_dump() for e in selected_campus],
    }

    existing_app = session.exec(
        select(ApplicationRecord).where(ApplicationRecord.job_id == job_id)
    ).first()

    if existing_app:
        existing_tailored = session.get(TailoredResumeRecord, existing_app.tailored_resume_id)
        if existing_tailored:
            existing_tailored.match_score = analysis.match_score
            existing_tailored.professional_summary = summary
            existing_tailored.selected_skills_json = dumps_json(selected_skills)
            existing_tailored.selected_experiences_json = dumps_json(selected_experiences_dict)
            existing_tailored.fit_strengths_json = dumps_json(fit_strengths)
            existing_tailored.fit_gaps_json = dumps_json(fit_gaps)
            existing_tailored.rendered_markdown = markdown
            session.add(existing_tailored)
            session.commit()
            session.refresh(existing_tailored)
            tailored_view = tailored_resume_record_to_view(existing_tailored)
            return PreparedApplicationResponse(
                job=job_view,
                analysis=analysis,
                tailored_resume=tailored_view,
                application=application_record_to_view(existing_app),
            )
    tailored_record = TailoredResumeRecord(
        job_id=job.id or 0,
        resume_profile_id=profile.id,
        match_score=analysis.match_score,
        professional_summary=summary,
        selected_skills_json=dumps_json(selected_skills),
        selected_experiences_json=dumps_json(selected_experiences_dict),
        fit_strengths_json=dumps_json(fit_strengths),
        fit_gaps_json=dumps_json(fit_gaps),
        rendered_markdown=markdown,
        created_at=utc_now(),
    )
    session.add(tailored_record)
    session.commit()
    session.refresh(tailored_record)

    application_record = ApplicationRecord(
        job_id=job.id or 0,
        tailored_resume_id=tailored_record.id or 0,
        platform=job.platform,
        status="draft",
        auto_supported=job.platform in AUTO_APPLY_PLATFORMS,
        target_url=job.source_url,
        notes=analysis.recommendation,
        created_at=utc_now(),
    )
    session.add(application_record)
    session.commit()
    session.refresh(application_record)

    tailored_view: TailoredResumeView = tailored_resume_record_to_view(tailored_record)
    return PreparedApplicationResponse(
        job=job_view,
        analysis=analysis,
        tailored_resume=tailored_view,
        application=application_record_to_view(application_record),
    )
