from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator, List

from sqlmodel import Session, SQLModel, create_engine, select

from app.config import get_settings
from app.models import ResumeProfileRecord


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dumps_json(values: List[object]) -> str:
    return json.dumps(values, ensure_ascii=False)


def loads_json(raw: str):
    if not raw:
        return []
    return json.loads(raw)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = session.exec(select(ResumeProfileRecord)).first()
        if existing:
            return

        seed_profile = {
            "personal_info": {
                "full_name": "Demo Candidate",
                "job_intention": "AI 应用开发工程师",
                "political_status": "",
                "birth_date": "",
                "hometown": "",
                "contact": "",
                "email": "",
                "hobbies": "",
                "strengths": "",
            },
            "self_evaluation": {
                "content": "偏向本地自动化、AI 工作流与数据处理的应用开发，关注真实经历驱动的简历定制与流程自动化。",
            },
            "education_background": [
                {
                    "school_name": "示例大学",
                    "attendance_period": "2021-2025",
                    "degree": "本科",
                    "ranking": "",
                    "major_courses": "",
                }
            ],
            "internship_experiences": [],
            "project_experiences": [
                {
                    "project_name": "校园创新项目",
                    "role": "全栈开发",
                    "duration": "2024-2025",
                    "summary": "负责本地 Web 工具的前后端实现与自动化流程编排。",
                    "skills": ["Python", "FastAPI", "React", "SQLite"],
                    "highlights": [
                        "搭建本地 Web 管理台，支持表单录入、状态追踪与结果导出。",
                        "将结构化数据处理流程封装为可复用的 API 服务。",
                    ],
                },
                {
                    "project_name": "数据分析实践",
                    "role": "Python 开发",
                    "duration": "2023-2024",
                    "summary": "使用 Python 处理文本数据并生成结构化报告。",
                    "skills": ["Python", "SQL", "Data Processing"],
                    "highlights": [
                        "编写文本清洗与字段提取脚本，提升信息整理效率。",
                        "输出结构化结果，便于后续检索和展示。",
                    ],
                },
                {
                    "project_name": "自动化脚本项目",
                    "role": "自动化工程实践",
                    "duration": "2024",
                    "summary": "围绕浏览器自动化和流程确认设计半自动执行方案。",
                    "skills": ["Playwright", "Automation", "Testing"],
                    "highlights": [
                        "实现需要人工确认节点的自动化流程设计，降低误操作风险。",
                        "整理执行日志与结果状态，便于后续复盘。",
                    ],
                },
            ],
            "campus_experiences": [],
            "honors_and_certificates": [],
            "training_experiences": [],
            "skills_and_other": {
                "skills": ["Python", "FastAPI", "SQL", "Playwright", "React", "Prompt Engineering", "LLM Integration"],
                "other": "",
            },
        }
        seed = ResumeProfileRecord(
            full_name="Demo Candidate",
            profile_json=json.dumps(seed_profile, ensure_ascii=False),
            updated_at=utc_now(),
        )
        session.add(seed)
        session.commit()
