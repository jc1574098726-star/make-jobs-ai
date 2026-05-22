from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db import dumps_json, get_session, utc_now
from app.models import JobRecord, RecommendedJobRecord, ResumeProfileRecord
from app.schemas import JobView, RecommendedJobView
from app.services.job_recommender import JobRecommenderService
from app.services.serializers import job_record_to_view, recommended_job_record_to_view, resume_record_to_view

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
recommender_service = JobRecommenderService()


@router.get("", response_model=List[RecommendedJobView])
def list_recommendations(session: Session = Depends(get_session)) -> List[RecommendedJobView]:
    records = session.exec(
        select(RecommendedJobRecord)
        .where(RecommendedJobRecord.status != "dismissed")
        .order_by(desc(RecommendedJobRecord.match_score), desc(RecommendedJobRecord.id))
    ).all()
    return [recommended_job_record_to_view(record) for record in records]


@router.post("/refresh", response_model=List[RecommendedJobView])
def refresh_recommendations(session: Session = Depends(get_session)) -> List[RecommendedJobView]:
    profile_record = session.exec(select(ResumeProfileRecord).order_by(desc(ResumeProfileRecord.id))).first()
    if not profile_record:
        raise HTTPException(status_code=400, detail="Resume profile is required before refreshing recommendations")

    profile = resume_record_to_view(profile_record)

    from app.routes.preferences import load_preferences
    prefs = load_preferences().model_dump()

    # Clear old non-dismissed recommendations before adding new ones
    old_records = session.exec(
        select(RecommendedJobRecord).where(RecommendedJobRecord.status != "dismissed")
    ).all()
    for old in old_records:
        session.delete(old)
    session.commit()

    for item in recommender_service.collect(profile, prefs):
        record = session.exec(
            select(RecommendedJobRecord).where(
                RecommendedJobRecord.platform == item["platform"],
                RecommendedJobRecord.source_url == item["source_url"],
            )
        ).first()
        if not record:
            record = RecommendedJobRecord(
                platform=item["platform"],
                source_url=item["source_url"],
                raw_text=item["raw_text"],
                job_title=item["job_title"],
                company_name=item["company_name"],
                city=item["city"],
                salary_range=item["salary_range"],
                skills_json=dumps_json(item["skills"]),
                highlights_json=dumps_json(item["highlights"]),
                match_score=item["analysis"].match_score,
                matched_skills_json=dumps_json(item["analysis"].matched_skills),
                missing_skills_json=dumps_json(item["analysis"].missing_skills),
                recommendation=item["analysis"].recommendation,
                status="new",
                created_at=utc_now(),
                last_seen_at=utc_now(),
            )
            session.add(record)
        else:
            record.raw_text = item["raw_text"]
            record.job_title = item["job_title"]
            record.company_name = item["company_name"]
            record.city = item["city"]
            record.salary_range = item["salary_range"]
            record.skills_json = dumps_json(item["skills"])
            record.highlights_json = dumps_json(item["highlights"])
            record.match_score = item["analysis"].match_score
            record.matched_skills_json = dumps_json(item["analysis"].matched_skills)
            record.missing_skills_json = dumps_json(item["analysis"].missing_skills)
            record.recommendation = item["analysis"].recommendation
            record.last_seen_at = utc_now()
            if record.status == "dismissed":
                record.status = "new"
            session.add(record)

    session.commit()
    records = session.exec(
        select(RecommendedJobRecord)
        .where(RecommendedJobRecord.status != "dismissed")
        .order_by(desc(RecommendedJobRecord.match_score), desc(RecommendedJobRecord.id)).limit(10)
    ).all()
    return [recommended_job_record_to_view(record) for record in records]


@router.post("/{recommendation_id}/dismiss")
def dismiss_recommendation(recommendation_id: int, session: Session = Depends(get_session)):
    record = session.get(RecommendedJobRecord, recommendation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    record.status = "dismissed"
    session.add(record)
    session.commit()
    return {"ok": True}


@router.post("/{recommendation_id}/import", response_model=JobView)
def import_recommendation(recommendation_id: int, session: Session = Depends(get_session)) -> JobView:
    record = session.get(RecommendedJobRecord, recommendation_id)
    if not record:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    job = JobRecord(
        platform=record.platform,
        source_url=record.source_url,
        raw_text=record.raw_text,
        job_title=record.job_title,
        company_name=record.company_name,
        city=record.city,
        salary_range=record.salary_range,
        experience_requirement=None,
        education_requirement=None,
        skills_json=record.skills_json,
        responsibilities_json="[]",
        highlights_json=record.highlights_json,
        created_at=utc_now(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    record.status = "imported"
    session.add(record)
    session.commit()
    return job_record_to_view(job)


@router.post("/clear")
def clear_recommendations(session: Session = Depends(get_session)):
    records = session.exec(
        select(RecommendedJobRecord).where(RecommendedJobRecord.status != "dismissed")
    ).all()
    for record in records:
        record.status = "dismissed"
        session.add(record)
    session.commit()
    return {"ok": True}
