from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from app.db import get_session
from app.models import ApplicationRecord, JobRecord, RecommendedJobRecord, ResumeProfileRecord
from app.schemas import OverviewResponse
from app.services.serializers import (
    application_record_to_view,
    job_record_to_view,
    recommended_job_record_to_view,
    resume_record_to_view,
)

router = APIRouter(tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview(session: Session = Depends(get_session)) -> OverviewResponse:
    profile_record = session.exec(select(ResumeProfileRecord).order_by(desc(ResumeProfileRecord.id))).first()
    jobs: List[JobRecord] = session.exec(select(JobRecord).order_by(desc(JobRecord.id))).all()
    applications: List[ApplicationRecord] = session.exec(select(ApplicationRecord).order_by(desc(ApplicationRecord.id))).all()
    recommended_jobs: List[RecommendedJobRecord] = session.exec(
        select(RecommendedJobRecord)
        .where(RecommendedJobRecord.status != "dismissed")
        .order_by(desc(RecommendedJobRecord.match_score), desc(RecommendedJobRecord.id)).limit(10)
    ).all()
    return OverviewResponse(
        profile=resume_record_to_view(profile_record) if profile_record else None,
        jobs=[job_record_to_view(job) for job in jobs],
        applications=[application_record_to_view(item) for item in applications],
        recommended_jobs=[recommended_job_record_to_view(item) for item in recommended_jobs],
    )
