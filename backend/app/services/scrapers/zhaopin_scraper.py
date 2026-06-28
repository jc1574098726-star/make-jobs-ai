from __future__ import annotations

import logging
from typing import Dict, List

from app.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ZhaopinScraper(BaseScraper):
    platform_id = "zhaopin"
    label = "智联招聘"

    # 智联招聘通过 UI 城市筛选，不使用 URL 参数，因此无需 city_codes

    def build_search_url(self, keyword: str, city_code: str) -> str:
        # jl 参数不可靠，必须通过 UI 筛选
        return f"https://sou.zhaopin.com/?jl=489&kw={keyword}&p=1"

    async def check_login(self, page) -> bool:
        try:
            body_text = await page.evaluate('document.body.innerText.substring(0, 3000)')
            if "我的简历" in body_text or "我的智联" in body_text or "退出" in body_text:
                return True
            if "登录/注册" in body_text:
                return False
            return True
        except Exception:
            return True

    async def apply_city_filter(self, page, city: str):
        """智联招聘的 UI 城市筛选。"""
        try:
            # 关闭登录弹窗
            try:
                close_btn = await page.query_selector('.zppp-panel-close')
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # 点击城市触发器
            city_trigger = await page.query_selector('.content-s__item__text--active')
            if not city_trigger:
                city_trigger = await page.query_selector('.content-s__item__text')
            if not city_trigger:
                logger.warning("Zhaopin: city trigger not found, URL: %s", page.url)
                return
            current_city = await city_trigger.text_content()
            logger.info("Zhaopin: current city='%s', target='%s'", current_city, city)
            if current_city and current_city.strip() == city:
                logger.info("Zhaopin: already on city '%s', skipping", city)
                return

            await city_trigger.click()
            await page.wait_for_timeout(2000)

            # 先试热门城市列表
            clicked = await page.evaluate("""
                (cityName) => {
                    const items = document.querySelectorAll('.query-city .list__item__text');
                    for (const item of items) {
                        if (item.textContent.trim() === cityName) {
                            item.click();
                            return true;
                        }
                    }
                    return false;
                }
            """, city)

            if clicked:
                logger.info("Zhaopin: clicked popular city '%s'", city)
                await page.wait_for_timeout(5000)
                return

            # 不在热门列表 → 搜索输入框
            search_input = await page.query_selector('.query-other-city__input')
            if not search_input:
                logger.warning("Zhaopin: search input not found")
                return

            logger.info("Zhaopin: typing '%s' in search input", city)
            await search_input.fill("")
            await search_input.type(city, delay=100)
            await page.wait_for_timeout(3000)

            result_count = await page.evaluate("""
                () => document.querySelectorAll('.query-other-city__list__item__a').length;
            """)
            logger.info("Zhaopin: found %d autocomplete results", result_count)

            if result_count == 0:
                logger.warning("Zhaopin: no autocomplete results for '%s'", city)
                return

            old_url = page.url

            result_clicked = await page.evaluate("""
                (cityName) => {
                    const items = document.querySelectorAll('.query-other-city__list__item__a');
                    for (const item of items) {
                        if (item.textContent.trim().includes(cityName)) {
                            item.click();
                            return 'matched: ' + item.textContent.trim();
                        }
                    }
                    if (items.length > 0) {
                        items[0].click();
                        return 'fallback: ' + items[0].textContent.trim();
                    }
                    return false;
                }
            """, city)

            if result_clicked:
                logger.info("Zhaopin: clicked result — %s, waiting for redirect...", result_clicked)
                try:
                    await page.wait_for_url(lambda url: url != old_url, timeout=10000)
                except Exception:
                    logger.debug("Zhaopin: URL did not change, waiting for load anyway")
                await page.wait_for_timeout(5000)
                logger.info("Zhaopin: page loaded, URL=%s", page.url)
            else:
                logger.warning("Zhaopin: no results for '%s'", city)
        except Exception as exc:
            logger.warning("Zhaopin city filter failed: %s", exc)

    async def extract_jobs(self, page, limit: int) -> List[Dict]:
        """智联招聘 DOM 抓取。"""
        await page.wait_for_selector(".joblist-box__item", timeout=15000)
        data = await page.evaluate("""
            (limit) => {
                const items = document.querySelectorAll('.joblist-box__item');
                const results = [];
                for (let i = 0; i < Math.min(items.length, limit); i++) {
                    const item = items[i];
                    const nameEl = item.querySelector('.jobinfo__name');
                    const title = nameEl ? nameEl.textContent.trim() : '';
                    const href = nameEl ? nameEl.href : '';
                    const salaryEl = item.querySelector('.jobinfo__salary');
                    const salary = salaryEl ? salaryEl.textContent.trim() : '';
                    const tagEls = item.querySelectorAll('.joblist-box__item-tag');
                    const tags = Array.from(tagEls).map(e => e.textContent.trim());
                    const compEl = item.querySelector('.companyinfo__name');
                    const company = compEl ? compEl.textContent.trim() : '';
                    const otherEls = item.querySelectorAll('.jobinfo__other-info-item');
                    const others = Array.from(otherEls).map(e => e.textContent.trim());
                    if (title) {
                        results.push({title, salary, tags, company, others, href});
                    }
                }
                return results;
            }
        """, limit)

        results = []
        for item in data:
            title = item.get("title", "")
            company = item.get("company", "")
            salary = item.get("salary", "")
            tags = item.get("tags", [])
            others = item.get("others", [])
            href = item.get("href", "")
            city = others[0] if others else ""
            experience = others[1] if len(others) > 1 else ""
            education = others[2] if len(others) > 2 else ""

            raw = f"{title}\n{company}\n{city}\n{salary}"
            if experience:
                raw += f"\n经验：{experience}"
            if education:
                raw += f"\n学历：{education}"
            if tags:
                raw += f"\n技能：{' '.join(tags[:5])}"

            results.append({
                "platform": "zhaopin",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })

        logger.info("Zhaopin: extracted %d jobs from DOM", len(results))
        return results
