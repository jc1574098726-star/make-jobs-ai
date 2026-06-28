"""URL 抓取调度器 — 根据平台配置选择抓取策略。"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re

from app.services.scrapers.base import USER_AGENT
from app.services.detail_fetchers import detect_fetcher

logger = logging.getLogger(__name__)

_GLOBAL_SELECTORS = ["article", "main", "[role='main']"]

NOISE_PATTERNS = re.compile(
    r"("
    r"登录|注册|首页|搜索|简历|消息|收藏|设置|退出|关注|粉丝|下载|App|"
    r"关于我们|联系我们|隐私政策|用户协议|帮助中心|意见反馈|"
    r"Copyright|©|All Rights Reserved|ICP备|备案号|"
    r"微信|扫码|分享|举报|投诉|"
    r"相关职位|相似职位|热门职位|最新职位|"
    r"查看全部|收起|展开更多|加载更多|"
    r"暂无|没有找到|无结果|"
    r"刚刚活跃|刚刚|活跃|人事主管|HR|Boss直聘|BOSS直聘|"
    r"感兴趣|立即沟通|投递简历|立即申请|"
    r"热门公司|猜你喜欢|为你推荐|看过的人还看过"
    r")",
    re.IGNORECASE,
)

RE_SALARY = re.compile(r"(\d[\d.]*[-~—至到]\d[\d.]*\s*[kK万](?:[/月年])?\s*(?:·\s*\d{1,2}薪)?(?:\s*\([\w]+\))?)")
RE_CITY = re.compile(
    r"(北京|上海|天津|重庆|深圳|广州|杭州|成都|武汉|苏州|南京|西安|长沙|郑州|合肥|"
    r"青岛|济南|大连|厦门|宁波|无锡|福州|昆明|哈尔滨|长春|沈阳|贵阳|南宁|兰州|"
    r"太原|石家庄|呼和浩特|乌鲁木齐|银川|西宁|拉萨|海口|珠海|佛山|东莞|中山|"
    r"惠州|温州|嘉兴|绍兴|金华|台州|常州|徐州|南通|扬州|镇江|泰州|盐城|连云港|"
    r"芜湖|蚌埠|漳州|泉州|烟台|潍坊|临沂|济宁|泰安|威海|日照|德州|聊城|滨州|"
    r"洛阳|安阳|新乡|焦作|许昌|南阳|商丘|信阳|周口|邯郸|秦皇岛|唐山|保定|张家口|"
    r"大同|运城|临汾|包头|鄂尔多斯|赤峰|通辽|吉林|四平|通化|齐齐哈尔|大庆|佳木斯|"
    r"绵阳|德阳|宜宾|泸州|遵义|六盘水|曲靖|大理|丽江|咸阳|宝鸡|渭南|延安|汉中|"
    r"兰州|天水|武威|银川|石嘴山|西宁|海东|"
    r"远程|海外|全国|不限)"
)


async def fetch_page_text(url: str, timeout: int = 30000) -> str:
    """根据平台配置抓取 URL 内容：requests 优先，Playwright fallback。"""
    import requests as req
    from bs4 import BeautifulSoup

    fetcher = detect_fetcher(url)
    logger.info("Detected platform: %s (%s)", fetcher.label, url[:80])

    selectors = fetcher.selectors + _GLOBAL_SELECTORS

    # Step 1: Try simple HTTP request (fast), skip if platform requires Playwright
    if not fetcher.force_playwright:
        try:
            resp = req.get(url, headers={"User-Agent": USER_AGENT}, timeout=10, proxies={"http": None, "https": None})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "title"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # Check if content has actual job data (salary patterns indicate real listings)
            has_job_data = RE_SALARY.search(text) or any(kw in text for kw in ["职责", "要求", "岗位", "任职"])
            if len(text) > 200 and has_job_data:
                logger.info("Fast HTTP fetch: %d chars", len(text))
                return _format_fields(text, url)
            logger.info("HTTP fetch: %d chars, no job data detected, trying Playwright", len(text))
        except Exception as exc:
            logger.info("HTTP fetch failed, trying Playwright: %s", exc)

    # Step 2: Fallback to Playwright
    return await _fetch_with_playwright(url, timeout, selectors, fetcher.use_body_text)


async def _safe_evaluate(page, expression, arg=None):
    """Evaluate JS on page, returning empty string on navigation errors."""
    try:
        if arg is not None:
            return await page.evaluate(expression, arg)
        return await page.evaluate(expression)
    except Exception:
        return ""


async def _fetch_with_playwright(url: str, timeout: int, selectors: list, use_body_text: bool) -> str:
    """Playwright fallback for JavaScript-heavy SPA sites."""
    from playwright.async_api import async_playwright

    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--no-sandbox"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=USER_AGENT,
            )
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # Smart wait: poll every 500ms, max 5 seconds
                # Some sites (BOSS) redirect during load, wait for stabilization
                for _ in range(10):
                    text = await _safe_evaluate(page, """() => {
                        const body = document.body;
                        return body && body.innerText ? body.innerText.length : 0;
                    }""")
                    if text > 100:
                        break
                    await page.wait_for_timeout(500)

                # Wait a bit more for SPA content to render
                await page.wait_for_timeout(1000)

                if use_body_text:
                    text = await _safe_evaluate(page, "() => document.body.innerText || ''")
                    if text and len(text) > 50:
                        logger.info("Body text extraction: %d chars", len(text))
                        return _format_fields(text, url)
                else:
                    for selector in selectors:
                        text = await _safe_evaluate(page, """(sel) => {
                            const el = document.querySelector(sel);
                            return el ? el.innerText.trim() : '';
                        }""", selector)
                        if text and len(text) > 50:
                            logger.info("Extracted via selector: %s (%d chars)", selector, len(text))
                            return _format_fields(text, url)

                # Fallback: full body text
                text = await _safe_evaluate(page, "() => document.body.innerText")
                return _format_fields(text, url)
            finally:
                await context.close()
    except Exception as exc:
        logger.debug("Playwright error: %s", exc)
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


def _clean_text(text: str) -> str:
    """Remove noise lines from page text."""
    hr_prefix_re = re.compile(r"^(招聘经理|招聘专员|HR|猎头|人事|女士|先生)\s*[··]\s*")
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) < 3:
            continue
        stripped = hr_prefix_re.sub("", stripped)
        if not stripped:
            continue
        if NOISE_PATTERNS.match(stripped):
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned)


def _format_fields(text: str, url: str = "") -> str:
    """Extract title, company, city, salary from page text and format as standard raw_text."""
    text = _clean_text(text)

    result = _extract_fields_with_claude(text)
    if result:
        return result

    lines = text.split("\n")
    title = ""
    company = ""
    city = ""
    salary = ""

    nav_re = re.compile(
        r"^(首页|职位|校园|海归|简历优化|猎聘APP|我是猎头|我是招聘方|登录|注册|"
        r"NEW|密码登录|获取验证码|登 录|同意|隐私|服务协议|搜索|IT|房地产|消费品|"
        r"汽车|医疗|邀请应聘|我的投递|我的收藏|投诉建议|更多|点击查看|名企职位|"
        r"投简历|聊一聊|收藏|分享|扫码|投递|沟通|感兴趣|立即|在线|已认证|"
        r"招聘经理|招聘专员|HR|猎头|女士|先生|小时前|刚刚|活跃|"
        r"最新发布|智能匹配|薪酬最高|清空筛选条件|职位类别|公司行业|"
        r"薪资要求|学历要求|工作经验|职位类型|公司性质|公司规模|"
        r"投递|立即投递|立即沟通|公司简介|职位介绍|其他信息|"
        r"职位推荐|城市频道|政企招聘|校园招聘|高端职位|海外招聘|驻外专区|"
        r"测评及培训|职Q社区|消息|我要招人|行政区|地铁沿线|"
        r"热门公司|猜你喜欢|为你推荐|看过的人还看过|相似职位)$",
        re.IGNORECASE,
    )
    # Also skip lines ending with common nav suffixes
    nav_suffix_re = re.compile(r"(站|频道|专区|社区|招聘)$")

    # Lines that look like filter options (salary ranges in sidebar, preceded by another salary-like line)
    filter_re = re.compile(r"^\d[\d.]*[-~—至到]?\d[\d.]*\s*[kK万]?$")

    # Special salary keywords
    salary_keywords_re = re.compile(r"(薪资面议|薪酬面议|待遇面议|工资面议)")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if nav_re.match(line):
            continue
        # Check i+1 ~ i+4 for salary (structure varies: title→salary, title→city→salary, etc.)
        for offset in range(1, 5):
            if i + offset < len(lines):
                next_line = lines[i + offset].strip()
                is_salary = RE_SALARY.search(next_line) or salary_keywords_re.search(next_line)
                if is_salary:
                    # Skip if next line looks like a filter option (salary preceded by another salary-like line)
                    if filter_re.match(next_line) and i > 0 and filter_re.match(lines[i - 1].strip()):
                        continue
                    title = line
                    if RE_SALARY.search(next_line):
                        salary = RE_SALARY.search(next_line).group(1).strip()
                    elif salary_keywords_re.search(next_line):
                        salary = salary_keywords_re.search(next_line).group(1)
                    # City is near the title/salary (check several lines after)
                    for city_offset in range(offset + 1, min(len(lines) - i, offset + 12)):
                        abs_idx = i + city_offset
                        loc_line = lines[abs_idx].strip()
                        if nav_re.match(loc_line) or nav_suffix_re.search(loc_line):
                            continue
                        city_m = RE_CITY.search(loc_line)
                        if city_m:
                            city = city_m.group(1)
                            break
                    break
        if title:
            break

    if not salary:
        salary_match = RE_SALARY.search(text)
        if salary_match:
            salary = salary_match.group(1).strip()

    if not city:
        city_match = RE_CITY.search(text)
        if city_match:
            city = city_match.group(1)

    hr_prefix_re = re.compile(r"^(招聘经理|招聘专员|HR|猎头|人事)\s*[··]\s*")
    for line in lines:
        line = line.strip()
        if nav_re.match(line):
            continue
        if any(kw in line for kw in ["有限公司", "集团", "股份", "公司"]):
            company = hr_prefix_re.sub("", line)
            break

    parts = []
    if title:
        parts.append(title)
    if company:
        parts.append(company)
    if city:
        parts.append(city)
    if salary:
        parts.append(salary)

    if parts:
        return "\n".join(parts)

    return text[:500]


def _extract_fields_with_claude(text: str) -> str:
    """Use Claude API to extract job fields. Returns formatted string or empty."""
    try:
        from app.services.claude_service import ClaudeService
        claude = ClaudeService._instance
        if not claude or not claude._client:
            return ""

        system_prompt = (
            "从以下网页文本中提取岗位信息，只输出以下5行（每行一个字段，不要标签）：\n"
            "第一行：岗位名称\n"
            "第二行：公司名称\n"
            "第三行：工作城市\n"
            "第四行：薪资范围\n"
            "如果某个字段无法确定，输出[未知]。不要输出其他任何内容。"
        )
        user_msg = f"网页文本：\n\n{text[:8000]}"

        if claude._api_format == "anthropic":
            response = claude._client.messages.create(
                model=claude._get_model(),
                max_tokens=500,
                system=[{"type": "text", "text": system_prompt}],
                messages=[{"role": "user", "content": user_msg}],
            )
            result_text = claude._collect_text(response.content)
        else:
            response = claude._client.chat.completions.create(
                model=claude._get_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=500,
            )
            result_text = response.choices[0].message.content or ""

        result_text = result_text.strip()
        if result_text and len(result_text.split("\n")) >= 2:
            return result_text
        return ""
    except Exception as exc:
        logger.debug("Claude field extraction skipped: %s", exc)
        return ""


def fetch_page_text_sync(url: str, timeout: int = 30000) -> str:
    """Sync wrapper for FastAPI endpoints."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(fetch_page_text(url, timeout))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(lambda: asyncio.run(fetch_page_text(url, timeout)))
        return future.result(timeout=60)


def extract_job_fields_with_ai(text: str) -> dict:
    """Use Claude API to extract structured job fields from page text.
    Returns dict with keys: job_title, company_name, city, salary_range.
    Returns empty dict on failure.
    """
    try:
        from app.services.claude_service import ClaudeService
        claude = ClaudeService._instance
        if not claude or not claude._client:
            return {}

        system_prompt = (
            "从以下网页文本中提取岗位信息，只输出以下4行（每行一个字段，不要标签）：\n"
            "第一行：岗位名称\n"
            "第二行：公司名称\n"
            "第三行：工作城市\n"
            "第四行：薪资范围\n"
            "如果某个字段无法确定，输出[未知]。不要输出其他任何内容。"
        )
        user_msg = f"网页文本：\n\n{text[:8000]}"

        if claude._api_format == "anthropic":
            response = claude._client.messages.create(
                model=claude._get_model(),
                max_tokens=500,
                system=[{"type": "text", "text": system_prompt}],
                messages=[{"role": "user", "content": user_msg}],
            )
            result_text = claude._collect_text(response.content)
        else:
            response = claude._client.chat.completions.create(
                model=claude._get_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=500,
            )
            result_text = response.choices[0].message.content or ""

        lines = [l.strip() for l in result_text.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            return {}

        def _clean(val: str) -> str:
            if val in ("[未知]", "未知", "无", "暂无", "N/A", "-"):
                return ""
            return val

        return {
            "job_title": _clean(lines[0]) if len(lines) > 0 else "",
            "company_name": _clean(lines[1]) if len(lines) > 1 else "",
            "city": _clean(lines[2]) if len(lines) > 2 else "",
            "salary_range": _clean(lines[3]) if len(lines) > 3 else "",
        }
    except Exception as exc:
        logger.debug("AI field extraction skipped: %s", exc)
        return {}
