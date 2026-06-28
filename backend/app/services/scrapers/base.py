from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

from app.config import BASE_DIR

logger = logging.getLogger(__name__)

CONTEXT_DIR = BASE_DIR / "data" / "browser_contexts"

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
delete navigator.__proto__.webdriver;
"""

ANTI_DETECT_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

LOGIN_WAIT_TIMEOUT = 120
LOGIN_POLL_INTERVAL = 3

PROVINCE_CAPITALS = {
    "北京市": "北京", "上海市": "上海", "天津市": "天津", "重庆市": "重庆",
    "河北省": "石家庄", "山西省": "太原", "辽宁省": "沈阳", "吉林省": "长春",
    "黑龙江省": "哈尔滨", "江苏省": "南京", "浙江省": "杭州", "安徽省": "合肥",
    "福建省": "福州", "江西省": "南昌", "山东省": "济南", "河南省": "郑州",
    "湖北省": "武汉", "湖南省": "长沙", "广东省": "广州", "海南省": "海口",
    "四川省": "成都", "贵州省": "贵阳", "云南省": "昆明", "陕西省": "西安",
    "甘肃省": "兰州", "青海省": "西宁", "台湾省": "台北",
    "内蒙古自治区": "呼和浩特", "广西壮族自治区": "南宁",
    "西藏自治区": "拉萨", "宁夏回族自治区": "银川", "新疆维吾尔自治区": "乌鲁木齐",
}


def _random_delay(low: float = 2.0, high: float = 4.0) -> None:
    time.sleep(random.uniform(low, high))


class BaseScraper(ABC):
    platform_id: str = ""
    label: str = ""

    city_codes: Dict[str, str] = {}
    route_patterns: List[str] = []  # 子类覆盖此属性以拦截特定 URL
    use_persistent_context: bool = True  # 子类可设为 False 使用非持久化浏览器

    def __init__(self, headed: bool = True):
        self._headed = headed

    # --- 子类必须实现 ---

    @abstractmethod
    def build_search_url(self, keyword: str, city_code: str) -> str:
        """构建搜索 URL。"""

    @abstractmethod
    async def check_login(self, page) -> bool:
        """检查当前页面是否已登录。True=已登录。"""

    @abstractmethod
    async def extract_jobs(self, page, limit: int) -> List[Dict]:
        """从页面提取职位列表。"""

    # --- 可选覆盖 ---

    async def apply_city_filter(self, page, city: str):
        """UI 城市筛选。默认不操作。"""
        pass

    async def on_response_text(self, url: str, body_text: str, captured_data: list):
        """API 响应拦截回调。接收 URL 和响应体文本。默认不操作。"""
        pass

    def get_city_code(self, city_name: str) -> str:
        """将中文城市名转为该平台的编码。"""
        if city_name in self.city_codes:
            return self.city_codes[city_name]
        capital = PROVINCE_CAPITALS.get(city_name)
        if capital and capital in self.city_codes:
            return self.city_codes[capital]
        for key, code in self.city_codes.items():
            if key in city_name or city_name in key:
                return code
        return ""

    # --- 共享方法 ---

    async def scrape(
        self, pw, keywords: List[str], cities: List[str], limit: int = 5,
    ) -> List[Dict]:
        """主入口：创建浏览器 context，遍历关键词×城市。"""
        if self.use_persistent_context:
            context_dir = CONTEXT_DIR / self.platform_id
            context_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Opening persistent context for %s", self.label)
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=str(context_dir),
                headless=False,
                args=ANTI_DETECT_ARGS,
                ignore_default_args=["--enable-automation"],
                viewport={"width": 1280, "height": 800},
                user_agent=USER_AGENT,
            )
        else:
            logger.info("Opening non-persistent context for %s", self.label)
            browser = await pw.chromium.launch(
                headless=False,
                args=ANTI_DETECT_ARGS,
                ignore_default_args=["--enable-automation"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=USER_AGENT,
            )
        await context.add_init_script(STEALTH_SCRIPT)

        all_results: List[Dict] = []
        seen_urls: set = set()

        try:
            for keyword in keywords:
                for city in (cities[:3] if cities else [""]):
                    try:
                        results = await self.scrape_search(
                            context, keyword, city, limit,
                        )
                        for job in results:
                            url = job.get("source_url", "")
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append(job)
                    except Exception as exc:
                        logger.warning(
                            "Scrape failed: %s/%s/%s: %s",
                            self.platform_id, keyword, city, exc,
                        )
                    _random_delay(3.0, 6.0)
        finally:
            await context.close()
            if not self.use_persistent_context:
                await browser.close()

        return all_results

    async def scrape_search(
        self, context, keyword: str, city: str, limit: int = 5,
    ) -> List[Dict]:
        """单次搜索：打开页面 → 检查登录 → 城市筛选 → 提取结果。"""
        city_code = self.get_city_code(city) if city else ""
        url = self.build_search_url(keyword, city_code)

        page = await context.new_page()
        captured_data: List[dict] = []
        self._captured_data = captured_data

        # 使用 response 事件捕获 API 响应体（route.fetch() 会丢失响应体）
        async def _on_response(response):
            try:
                url = response.url
                if not any(
                    p.replace("**", "") in url
                    for p in self.route_patterns
                ):
                    return
                body_text = await response.text()
                if hasattr(self, "on_response_text"):
                    await self.on_response_text(url, body_text, captured_data)
            except Exception as exc:
                logger.debug("Response capture skipped: %s", exc)

        page.on("response", _on_response)

        try:
            logger.info("Navigating to: %s", url)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.bring_to_front()
            await page.wait_for_timeout(10000)

            # 登录检查
            logged_in = await self.check_login(page)
            if not logged_in:
                logger.info(
                    "%s 未登录，请在浏览器中完成登录（等待%d秒）...",
                    self.label, LOGIN_WAIT_TIMEOUT,
                )
                await self._show_login_banner(page, LOGIN_WAIT_TIMEOUT)
                logged_in = await self._wait_for_login(page)
                if not logged_in:
                    logger.info("%s 登录超时，跳过抓取", self.label)
                    return []

            # UI 城市筛选
            if city:
                await self.apply_city_filter(page, city)
                await page.wait_for_timeout(3000)

            # 提取结果（子类实现）
            return await self.extract_jobs(page, limit)

        except Exception as exc:
            logger.warning("Navigation error: %s", exc)
            return []
        finally:
            await page.close()

    async def _wait_for_login(self, page, timeout: int = LOGIN_WAIT_TIMEOUT) -> bool:
        elapsed = 0
        refresh_count = 0
        while elapsed < timeout:
            await page.wait_for_timeout(LOGIN_POLL_INTERVAL * 1000)
            elapsed += LOGIN_POLL_INTERVAL

            refresh_count += 1
            if refresh_count % 5 == 0:
                try:
                    current_url = page.url
                    await page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(3000)
                    await self._show_login_banner(page, max(0, timeout - elapsed))
                except Exception:
                    pass

            logged_in = await self.check_login(page)
            if logged_in:
                logger.info("%s 登录成功！", self.platform_id)
                await self._remove_login_banner(page)
                return True
            remaining = timeout - elapsed
            if remaining > 0:
                logger.info("等待登录中... 剩余 %d 秒", remaining)
                await self._update_login_banner(page, remaining)
        return False

    async def _show_login_banner(self, page, timeout: int):
        banner_js = f"""
        (() => {{
            const old = document.getElementById('__login_banner__');
            if (old) old.remove();
            const div = document.createElement('div');
            div.id = '__login_banner__';
            div.style.cssText = 'position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:999999;background:#e74c3c;color:#fff;padding:10px 28px;font-size:14px;font-weight:bold;text-align:center;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.3);white-space:nowrap;';
            div.innerText = '⚠ {self.label} 未登录 — 请在此页面完成登录（{timeout}秒后自动跳过）';
            document.body.appendChild(div);
        }})();
        """
        try:
            await page.evaluate(banner_js)
        except Exception:
            pass

    async def _update_login_banner(self, page, remaining: int):
        try:
            await page.evaluate(f"""
                (() => {{
                    const el = document.getElementById('__login_banner__');
                    if (el) el.innerText = '⚠ 请在此页面完成登录（剩余 {remaining} 秒后自动跳过）';
                }})();
            """)
        except Exception:
            pass

    async def _remove_login_banner(self, page):
        try:
            await page.evaluate("""
                (() => {
                    const el = document.getElementById('__login_banner__');
                    if (el) el.remove();
                })();
            """)
        except Exception:
            pass
