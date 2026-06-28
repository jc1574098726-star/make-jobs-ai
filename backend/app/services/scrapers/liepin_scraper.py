from __future__ import annotations

import json as _json
import logging
from typing import Dict, List

from app.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LiepinScraper(BaseScraper):
    platform_id = "liepin"
    label = "猎聘"

    # 猎聘筛选栏可见城市（通过页面 li[data-key="dq"] 的 data-name 属性提取）
    # 这些城市可以直接点击筛选栏选择，无需打开"其他"弹窗
    VISIBLE_CITIES = {
        "全国", "北京", "上海", "天津", "重庆",
        "广州", "深圳", "苏州", "南京", "杭州",
        "大连", "成都", "武汉", "西安",
    }

    # 反爬验证滑块检测选择器
    CAPTCHA_SELECTORS = [
        ".captcha-modal",
        ".verify-wrap",
        ".slide-verify",
        "#captcha",
        ".yidun",
        ".geetest_panel",
        '[class*="captcha"]',
        '[class*="slider-verify"]',
        '[class*="verify-wrap"]',
    ]

    def build_search_url(self, keyword: str, city_code: str) -> str:
        return f"https://www.liepin.com/zhaopin/?key={keyword}"

    async def check_login(self, page) -> bool:
        return True

    async def _wait_for_captcha(self, page, timeout_ms: int = 120000) -> bool:
        """检测反爬验证滑块，如有则暂停等待用户手动滑动。返回 True 表示验证通过。"""
        found = await page.evaluate("""
            (selectors) => {
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.getBoundingClientRect().width > 0) {
                        return sel;
                    }
                }
                return null;
            }
        """, self.CAPTCHA_SELECTORS)

        if not found:
            return True

        logger.warning("Liepin: 检测到反爬验证（%s），请在浏览器中手动完成滑块验证...", found)
        print(f"\n{'='*60}")
        print(f"[猎聘] 检测到反爬验证，请在浏览器中手动滑动滑块完成验证")
        print(f"[猎聘] 等待验证完成（最多 {timeout_ms // 1000} 秒）...")
        print(f"{'='*60}\n")

        # 轮询检测验证是否消失
        elapsed = 0
        interval = 2000
        while elapsed < timeout_ms:
            await page.wait_for_timeout(interval)
            elapsed += interval

            still_exists = await page.evaluate("""
                (selectors) => {
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.getBoundingClientRect().width > 0) {
                            return true;
                        }
                    }
                    return false;
                }
            """, self.CAPTCHA_SELECTORS)

            if not still_exists:
                logger.info("Liepin: 验证已通过")
                print("[猎聘] 验证已通过，继续执行...")
                return True

        logger.warning("Liepin: 等待验证超时")
        print("[猎聘] 等待验证超时，继续尝试...")
        return False

    async def apply_city_filter(self, page, city: str):
        """猎聘 UI 城市筛选：点击筛选栏城市 li，不在列表中则打开"其他"弹窗搜索。"""
        try:
            # 关闭登录弹窗（如有）
            try:
                close_btn = await page.query_selector('.modal-close, .dialog-close, .close-btn')
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # 检查当前选中的城市
            current_raw = await page.evaluate("""
                () => {
                    const sel = document.querySelector('li[data-key="dq"].selected');
                    return sel ? sel.getAttribute('data-name') : null;
                }
            """)
            logger.info("[liepin] 当前城市: '%s', 目标: '%s'", current_raw, city)
            if current_raw and (current_raw == city or current_raw.endswith("·" + city)):
                logger.info("[liepin] 已选中城市 '%s'，跳过", city)
                return

            # 尝试直接点击筛选栏中的城市 li 项
            clicked = await page.evaluate("""
                (cityName) => {
                    const items = document.querySelectorAll('li[data-key="dq"]');
                    for (const item of items) {
                        const name = item.getAttribute('data-name') || '';
                        if (name === cityName || name.endsWith('·' + cityName)) {
                            item.click();
                            return name;
                        }
                    }
                    return false;
                }
            """, city)

            if clicked:
                logger.info("[liepin] 点击筛选栏城市 '%s'", clicked)
                await page.wait_for_timeout(5000)
                return

            # 不在筛选栏 → 打开"其他"弹窗，通过搜索选择城市
            logger.info("[liepin] 城市 '%s' 不在筛选栏，打开弹窗搜索", city)
            await self._apply_city_via_modal(page, city)

        except Exception as exc:
            logger.warning("[liepin] city filter failed: %s", exc)

    async def _apply_city_via_modal(self, page, city: str):
        """通过"其他"弹窗搜索并选择城市。"""
        logger.info("[liepin] 打开城市弹窗，搜索 '%s'", city)
        # 点击"其他"按钮打开城市弹窗
        try:
            await page.click('#filter-option-other-city', timeout=5000)
        except Exception:
            logger.warning("[liepin] 无法点击'其他'按钮")
            return
        await page.wait_for_timeout(3000)

        # 检测是否出现反爬验证
        await self._wait_for_captcha(page)

        # 在弹窗搜索框中输入城市名
        search_input = await page.query_selector('.ant-modal.city-modal .ant-input')
        if not search_input:
            logger.warning("[liepin] 弹窗搜索框未找到")
            return

        await search_input.click()
        await search_input.fill("")
        await search_input.type(city, delay=150)
        await page.wait_for_timeout(2000)

        # 点击搜索结果（格式为"省份·城市"）
        result = await page.evaluate("""
            () => {
                const suggestList = document.querySelector('.ant-modal.city-modal .suggest-list');
                if (!suggestList) return 'no suggest-list';
                const li = suggestList.querySelector('li');
                if (!li) return 'no li';
                const p = li.querySelector('p');
                if (p) {
                    p.click();
                    return 'clicked: ' + p.textContent.trim();
                }
                li.click();
                return 'clicked li: ' + li.textContent.trim();
            }
        """)
        logger.info("[liepin] 搜索结果: %s", result)

        if result.startswith("clicked"):
            await page.wait_for_timeout(8000)
        else:
            logger.warning("[liepin] 搜索结果未找到 '%s' (%s)", city, result)

    async def on_response(self, response, captured_data: list):
        resp_url = response.url
        if "pc-search-job" not in resp_url or "cond-init" in resp_url:
            return
        try:
            raw = await response.body()
            body = _json.loads(raw)
            logger.info("[liepin] API 响应: %s", resp_url[:80])

            if isinstance(body, dict):
                data_block = body.get("data", {})
                if isinstance(data_block, dict):
                    jobs = data_block.get("jobCardList", [])
                    if not jobs:
                        jobs = data_block.get("list", [])
                    if not jobs:
                        jobs = data_block.get("jobList", [])
                    inner = data_block.get("data", {})
                    if not jobs and isinstance(inner, dict):
                        jobs = inner.get("jobCardList", [])
                        if not jobs:
                            jobs = inner.get("list", [])
            elif isinstance(body, list):
                jobs = body
            else:
                jobs = []
            if jobs:
                captured_data.clear()
                captured_data.extend(jobs)
                first_city = ""
                if jobs:
                    j = jobs[0].get("job", jobs[0])
                    first_city = j.get("dq", "") or j.get("jobCity", "")
                logger.info("[liepin] 捕获 %d 条数据, 首条城市=%s", len(jobs), first_city)
        except Exception as exc:
            logger.debug("[liepin] response parse error: %s", exc)

    async def extract_jobs(self, page, limit: int) -> List[Dict]:
        if hasattr(self, "_captured_data") and self._captured_data:
            return self._parse_jobs(self._captured_data)[:limit]
        return []

    async def scrape_search(
        self, context, keyword: str, city: str, limit: int = 5,
    ) -> List[Dict]:
        """猎聘搜索：导航到搜索页，通过 UI 进行城市筛选。"""
        url = self.build_search_url(keyword, "")
        page = await context.new_page()
        self._captured_data: List[dict] = []

        async def _on_response(response):
            try:
                if response.status != 200:
                    return
                await self.on_response(response, self._captured_data)
            except Exception as exc:
                logger.debug("Response capture skipped: %s", exc)

        page.on("response", _on_response)

        try:
            logger.info("[liepin] 导航到: %s (keyword=%s, city=%s)", url, keyword, city)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.bring_to_front()
            await page.wait_for_timeout(10000)

            logger.info("[liepin] 初始抓取: %d 条数据", len(self._captured_data))

            # 检测反爬验证
            await self._wait_for_captcha(page)

            if city:
                self._captured_data.clear()
                await self.apply_city_filter(page, city)
                await page.wait_for_timeout(8000)
                logger.info("[liepin] 城市筛选后: %d 条数据", len(self._captured_data))
            else:
                await page.wait_for_timeout(8000)

            if self._captured_data:
                results = self._parse_jobs(self._captured_data)[:limit]
                logger.info("[liepin] 返回 %d 条结果", len(results))
                return results
            logger.warning("[liepin] 没有抓取到数据")
            return []
        except Exception as exc:
            logger.warning("[liepin] navigation error: %s", exc)
            if self._captured_data:
                return self._parse_jobs(self._captured_data)[:limit]
            return []
        finally:
            await page.close()

    def _parse_jobs(self, data) -> List[Dict]:
        results = []
        job_list = data if isinstance(data, list) else []

        for item in job_list:
            job = item.get("job", item) if isinstance(item, dict) else item
            comp = item.get("comp", {}) if isinstance(item, dict) else {}

            title = job.get("title", "")
            company = comp.get("compName", "") or job.get("compName", "")
            city = job.get("dq", "") or job.get("jobCity", "")
            salary = job.get("salary", "") or job.get("salaryDesc", "")
            job_id = job.get("jobId", "") or job.get("lid", "")
            link = job.get("link", "") or (f"https://www.liepin.com/job/{job_id}" if job_id else "")
            experience = job.get("requireWorkYears", "")
            education = job.get("requireEduLevel", "")

            labels = job.get("labels", [])
            skills = " ".join(str(l) for l in labels[:5]) if isinstance(labels, list) else ""

            raw = f"{title}\n{company}\n{city}\n{salary}"
            if experience:
                raw += f"\n经验：{experience}"
            if education:
                raw += f"\n学历：{education}"
            if skills:
                raw += f"\n技能：{skills}"

            results.append({
                "platform": "liepin",
                "source_url": link,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })
        return results
