from __future__ import annotations

import json
from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import BASE_DIR

router = APIRouter(prefix="/preferences", tags=["preferences"])

PREFERENCES_PATH = BASE_DIR / "data" / "job_preferences.json"


class JobPreferences(BaseModel):
    regions: List[str] = []
    overseas: bool = False
    industry: List[str] = []
    job_titles: List[str] = []
    platforms: List[str] = ["boss"]
    parse_mode: str = "local"  # "local" = 本地解析, "api" = 调用API


def _load() -> Dict:
    if PREFERENCES_PATH.exists():
        try:
            return json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save(data: Dict) -> None:
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCES_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_preferences() -> JobPreferences:
    data = _load()
    return JobPreferences(
        regions=data.get("regions", [])[:3],
        overseas=data.get("overseas", False),
        industry=data.get("industry", [])[:3],
        job_titles=data.get("job_titles", [])[:3],
        platforms=data.get("platforms", ["boss"])[:2],
        parse_mode=data.get("parse_mode", "local"),
    )


@router.get("", response_model=JobPreferences)
def get_preferences() -> JobPreferences:
    return load_preferences()


@router.put("", response_model=JobPreferences)
def update_preferences(payload: JobPreferences) -> JobPreferences:
    platforms = payload.platforms[:2] if payload.platforms else ["boss"]
    data = {
        "regions": payload.regions[:3],
        "overseas": payload.overseas,
        "industry": payload.industry[:3],
        "job_titles": payload.job_titles[:3],
        "platforms": platforms,
        "parse_mode": payload.parse_mode if payload.parse_mode in ("local", "api") else "local",
    }
    _save(data)
    return JobPreferences(**data)
