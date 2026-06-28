from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db import get_session, utc_now
from app.models import ApplicationRecord
from app.schemas import ApplicationView
from app.services.serializers import application_record_to_view

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=List[ApplicationView])
def list_applications(session: Session = Depends(get_session)) -> List[ApplicationView]:
    records = session.exec(select(ApplicationRecord).order_by(desc(ApplicationRecord.id))).all()
    return [application_record_to_view(record) for record in records]


@router.get("/{application_id}", response_model=ApplicationView)
def get_application(application_id: int, session: Session = Depends(get_session)) -> ApplicationView:
    record = session.get(ApplicationRecord, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    return application_record_to_view(record)


@router.post("/{application_id}/confirm", response_model=ApplicationView)
def confirm_application(application_id: int, session: Session = Depends(get_session)) -> ApplicationView:
    record = session.get(ApplicationRecord, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    record.status = "confirmed"
    record.confirmed_at = utc_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return application_record_to_view(record)
