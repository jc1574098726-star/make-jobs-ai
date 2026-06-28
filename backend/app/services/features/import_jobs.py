"""岗位导入功能 — URL 抓取 + AI 字段提取 + 入库。"""
from __future__ import annotations

from app.services.url_fetcher import extract_job_fields_with_ai, fetch_page_text_sync

# Platforms with strong anti-bot that require manual paste
_NO_FETCH_PLATFORMS = {
    "boss": "BOSS直聘有反爬验证，无法自动读取。请在浏览器中打开链接，复制岗位内容粘贴到下方",
}


def import_from_url(url: str) -> dict:
    """从 URL 抓取岗位内容并提取结构化字段。"""
    from app.services.detail_fetchers import detect_fetcher
    fetcher = detect_fetcher(url)

    if fetcher.platform_id in _NO_FETCH_PLATFORMS:
        return {"raw_text": "", "error": _NO_FETCH_PLATFORMS[fetcher.platform_id]}

    raw_text = fetch_page_text_sync(url)
    if not raw_text:
        return {"raw_text": "", "error": "该链接无法自动读取（可能有反爬验证），请手动复制岗位内容粘贴到下方"}

    fields = extract_job_fields_with_ai(raw_text)
    return {"raw_text": raw_text, **fields}
