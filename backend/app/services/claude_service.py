from __future__ import annotations

import json
from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel

from app.config import get_settings
from app.schemas import (
    AIParsedJob,
    AIResumeSummary,
    JobView,
    MatchAnalysis,
    ResumeProfileInput,
    ResumeProfileView,
)


T = TypeVar("T", bound=BaseModel)


JOB_PARSE_SYSTEM_PROMPT = """
你是一个中文招聘信息结构化助手。

目标：根据用户提供的岗位原文，提取结构化岗位信息，并严格返回 JSON。

要求：
1. 只能依据输入中明确出现的信息提取，不要编造。
2. 不确定的字段返回 null，列表字段返回 []。
3. 保留中文原意，技能标签尽量简洁，例如 Python、FastAPI、SQL、React。
4. responsibilities 提炼 3-5 条职责要点，highlights 提炼 0-4 条岗位亮点。
5. 输出必须是单个 JSON 对象，字段必须与 schema 完全一致，不要输出解释文字或 Markdown。
""".strip()


RESUME_SUMMARY_SYSTEM_PROMPT = """
你是一个中文求职简历定制助手。

目标：基于候选人的真实资料、岗位信息、匹配分析和已选经历，生成定制简历摘要。

硬性约束：
1. 只能使用输入中已经存在的真实经历、技能、角色、项目与事实。
2. 不得编造新的公司、项目、技术、成绩、年限、职责或量化结果。
3. professional_summary 控制在 2-3 句，适合放在简历开头。
4. fit_strengths 输出 2-4 条，每条聚焦真实匹配点。
5. fit_gaps 输出 1-3 条，如果没有明显缺口可输出说明候选人已具备较高贴合度。
6. 输出必须是单个 JSON 对象，字段必须与 schema 完全一致，不要输出解释文字或 Markdown。
""".strip()


RESUME_PARSE_SYSTEM_PROMPT = """
你是一个中文简历结构化助手。

目标：根据用户上传的简历原文，提取出可直接写入简历资料库的板块化结构化 JSON。

硬性约束：
1. 只能使用简历中明确出现的信息，不得编造公司、项目、技能、教育、成绩、时间或量化结果。
2. 如果某板块或字段无法确认，字符串填空字符串 ""，列表填 []，不要编造。
3. 简历分为以下板块，都不是必填项，缺失的板块留空即可：
   - personal_info：姓名 full_name、求职意向 job_intention、政治面貌 political_status、出生年月 birth_date、籍贯 hometown、联系方式 contact、邮箱 email、兴趣爱好 hobbies、个人特长 strengths
   - self_evaluation：自我评价 content
   - education_background：教育背景列表，每项含 school_name、attendance_period、degree、ranking、major_courses
   - internship_experiences：实习经历列表，每项含 company、role、duration、summary、skills、highlights
   - project_experiences：项目经历列表，每项含 project_name、role、duration、summary、skills、highlights
   - campus_experiences：校园经历列表，每项含 organization、role、duration、summary、highlights
   - honors_and_certificates：荣誉证书列表，每项含 name、time、issuer
   - training_experiences：培训经历列表，每项含 course_name、institution、duration、summary
   - skills_and_other：技能及其他，含 skills 列表和 other 文本
4. 求职意向 job_intention 根据简历中的求职方向、岗位标题、经历内容归纳，不要脱离原文扩展。
5. 输出必须是单个 JSON 对象，字段必须与 schema 完全一致，不要输出解释文字或 Markdown。
""".strip()


MATCH_ANALYSIS_SYSTEM_PROMPT = """
你是一个中文求职匹配度分析助手。

目标：根据候选人的简历资料和目标岗位信息，分析匹配度并给出结构化评价。

分析维度：
1. 技能匹配：对比简历技能与岗位要求，评估覆盖度
2. 经验匹配：评估实习/项目/校园经历与岗位职责的相关性
3. 学历匹配：评估学历是否满足岗位要求
4. 整体匹配度评分：0-100 分

硬性约束：
1. 只能基于输入的简历资料和岗位信息进行分析，不得编造
2. match_score 范围 0-100，需合理反映匹配程度
3. matched_skills 列出简历中明确覆盖的岗位技能
4. missing_skills 列出岗位要求但简历未覆盖的技能
5. strengths 列出 2-4 条匹配优势，每条具体且基于真实经历
6. gaps 列出 1-3 条不足或改进建议
7. recommendation 给出一段简短的求职建议（1-2 句话）
8. 输出必须是单个 JSON 对象，字段必须与 schema 完全一致，不要输出解释文字或 Markdown。
""".strip()


BEAUTIFY_RESUME_SYSTEM_PROMPT = """
你是一个专业的中文简历美化助手。

目标：基于候选人的真实简历资料，生成一份排版精美、语言流畅、亮点突出的美化简历。

硬性约束：
1. 只能使用输入中已经存在的真实经历、技能、角色、项目与事实。
2. 不得编造新的公司、项目、技术、成绩、年限、职责或量化结果。
3. 优化语言表达，使描述更专业、更有冲击力，但不改变事实本身。
4. 合理组织板块顺序，突出核心竞争力。
5. 输出格式为 Markdown，适合直接阅读或复制到 Word。
6. 包含以下板块（有内容才输出）：个人信息、求职意向、自我评价、教育背景、实习经历、项目经历、校园经历、荣誉证书、培训经历、技能及其他。
""".strip()


MARKET_RESUME_SYSTEM_PROMPT = """
你是一个资深的中文求职市场顾问和简历优化专家。

目标：基于候选人的真实简历资料，生成一份针对当前就业市场需求优化的专业简历，突出候选人的市场竞争力。

硬性约束：
1. 只能使用输入中已经存在的真实经历、技能、角色、项目与事实。
2. 不得编造新的公司、项目、技术、成绩、年限、职责或量化结果。
3. 根据候选人的技能和经历方向，推测最匹配的岗位类型，并针对性优化简历措辞。
4. 突出市场需求旺盛的技能和经验，用行业术语提升专业感。
5. 自我评价部分需体现对行业趋势的理解和自身价值定位。
6. 输出格式为 Markdown，适合直接阅读或复制到 Word。
7. 包含以下板块（有内容才输出）：个人信息、求职意向、自我评价、教育背景、实习经历、项目经历、校园经历、荣誉证书、培训经历、技能及其他。
""".strip()


class ClaudeService:
    _instance = None

    def __init__(self) -> None:
        ClaudeService._instance = self
        self._settings = get_settings()
        self._client = None
        self._api_format = "anthropic"
        self._build_client()

    def _build_client(self) -> None:
        from app.routes.settings import get_user_api_key, get_user_api_base_url, get_user_provider
        from app.services.providers import get_provider

        provider_id = get_user_provider()
        provider = get_provider(provider_id)
        self._api_format = provider["api_format"]

        api_key = get_user_api_key()
        base_url = get_user_api_base_url() or provider["base_url"]

        if not api_key and self._settings.anthropic_api_key:
            api_key = self._settings.anthropic_api_key

        if not api_key:
            self._client = None
            return

        if self._api_format == "anthropic":
            import anthropic
            kwargs = {"api_key": api_key}
            if base_url and base_url != "https://api.anthropic.com":
                kwargs["base_url"] = base_url
            self._client = anthropic.Anthropic(**kwargs)
        else:
            import openai
            self._client = openai.OpenAI(api_key=api_key, base_url=base_url)

    @classmethod
    def reinit(cls) -> None:
        if cls._instance:
            cls._instance._build_client()

    def _get_model(self) -> str:
        from app.routes.settings import get_user_model
        user_model = get_user_model()
        return user_model or self._settings.claude_model

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def parse_job(self, raw_text: str, heuristic_candidate: AIParsedJob) -> AIParsedJob:
        payload = {
            "schema": AIParsedJob.model_json_schema(),
            "raw_text": raw_text,
            "heuristic_candidate": heuristic_candidate.model_dump(),
        }
        return self._request_json(
            system_prompt=JOB_PARSE_SYSTEM_PROMPT,
            user_payload=payload,
            response_model=AIParsedJob,
            max_tokens=1400,
        )

    def parse_resume_profile(self, raw_text: str) -> ResumeProfileInput:
        payload = {
            "schema": ResumeProfileInput.model_json_schema(),
            "raw_text": raw_text,
        }
        return self._request_json(
            system_prompt=RESUME_PARSE_SYSTEM_PROMPT,
            user_payload=payload,
            response_model=ResumeProfileInput,
            max_tokens=3000,
        )

    def summarize_resume(
        self,
        profile: ResumeProfileView,
        job: JobView,
        analysis: MatchAnalysis,
        selected_skills: List[str],
        selected_experiences: List[Dict],
    ) -> AIResumeSummary:
        payload = {
            "schema": AIResumeSummary.model_json_schema(),
            "profile": profile.model_dump(),
            "job": job.model_dump(),
            "analysis": analysis.model_dump(),
            "selected_skills": selected_skills,
            "selected_experiences": selected_experiences,
        }
        return self._request_json(
            system_prompt=RESUME_SUMMARY_SYSTEM_PROMPT,
            user_payload=payload,
            response_model=AIResumeSummary,
            max_tokens=1600,
        )

    def analyze_match(
        self,
        profile: ResumeProfileView,
        job_skills: List[str],
        responsibilities: List[str],
        job_title: str = "",
        company_name: str = "",
    ) -> MatchAnalysis:
        payload = {
            "schema": MatchAnalysis.model_json_schema(),
            "resume_profile": profile.model_dump(),
            "job_title": job_title,
            "company_name": company_name,
            "job_skills": job_skills,
            "responsibilities": responsibilities,
        }
        return self._request_json(
            system_prompt=MATCH_ANALYSIS_SYSTEM_PROMPT,
            user_payload=payload,
            response_model=MatchAnalysis,
            max_tokens=1200,
        )

    def generate_beautified_resume(self, profile: ResumeProfileView) -> str:
        return self._request_markdown(
            system_prompt=BEAUTIFY_RESUME_SYSTEM_PROMPT,
            user_payload={"profile": profile.model_dump()},
            max_tokens=4000,
        )

    def generate_market_resume(self, profile: ResumeProfileView) -> str:
        return self._request_markdown(
            system_prompt=MARKET_RESUME_SYSTEM_PROMPT,
            user_payload={"profile": profile.model_dump()},
            max_tokens=4000,
        )

    def _request_markdown(self, system_prompt: str, user_payload: Dict, max_tokens: int) -> str:
        if not self._client:
            raise RuntimeError("API key is not configured")

        if self._api_format == "anthropic":
            response = self._client.messages.create(
                model=self._get_model(),
                max_tokens=max_tokens,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True, indent=2),
                    }
                ],
            )
            parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
            text = "\n".join(parts).strip()
        else:
            response = self._client.chat.completions.create(
                model=self._get_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True, indent=2),
                    },
                ],
                max_tokens=max_tokens,
            )
            text = (response.choices[0].message.content or "").strip()

        if not text:
            raise ValueError("API did not return any content")
        return text

    def _request_json(
        self,
        system_prompt: str,
        user_payload: Dict,
        response_model: Type[T],
        max_tokens: int,
    ) -> T:
        if not self._client:
            raise RuntimeError("API key is not configured")

        if self._api_format == "anthropic":
            return self._request_json_anthropic(system_prompt, user_payload, response_model, max_tokens)
        else:
            return self._request_json_openai(system_prompt, user_payload, response_model, max_tokens)

    def _request_json_anthropic(
        self,
        system_prompt: str,
        user_payload: Dict,
        response_model: Type[T],
        max_tokens: int,
    ) -> T:
        response = self._client.messages.create(
            model=self._get_model(),
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True, indent=2),
                }
            ],
        )
        content = self._collect_text(response.content)
        return self._parse_json_response(content, response_model)

    def _request_json_openai(
        self,
        system_prompt: str,
        user_payload: Dict,
        response_model: Type[T],
        max_tokens: int,
    ) -> T:
        response = self._client.chat.completions.create(
            model=self._get_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True, indent=2),
                },
            ],
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content
        if not text:
            raise ValueError("API response did not include text content")
        return self._parse_json_response(text, response_model)

    def _parse_json_response(self, text: str, response_model: Type[T]) -> T:
        json_str = self._extract_json_object(text)
        data = json.loads(json_str)
        return response_model.model_validate(data)

    def _collect_text(self, blocks: List[object]) -> str:
        parts: List[str] = []
        for block in blocks:
            if getattr(block, "type", None) == "text":
                parts.append(getattr(block, "text", ""))
        combined = "\n".join(part for part in parts if part).strip()
        if not combined:
            raise ValueError("Claude response did not include text content")
        return combined

    def _extract_json_object(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("API response did not contain a JSON object")
        return stripped[start : end + 1]
