from __future__ import annotations

import logging
from typing import Dict, List

from app.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LinkedinScraper(BaseScraper):
    platform_id = "linkedin"
    label = "LinkedIn"
    use_persistent_context = False  # 领英不用持久化浏览器，避免继承系统 Chrome 的 Google 账号

    # LinkedIn 使用英文城市名，中文→英文映射（作为 city_codes 使用）
    city_codes: Dict[str, str] = {
        "北京": "Beijing", "上海": "Shanghai", "天津": "Tianjin", "重庆": "Chongqing",
        "石家庄": "Shijiazhuang", "唐山": "Tangshan", "秦皇岛": "Qinhuangdao", "邯郸": "Handan",
        "邢台": "Xingtai", "保定": "Baoding", "张家口": "Zhangjiakou", "承德": "Chengde",
        "沧州": "Cangzhou", "廊坊": "Langfang", "衡水": "Hengshui",
        "太原": "Taiyuan", "大同": "Datong", "阳泉": "Yangquan", "长治": "Changzhi",
        "晋城": "Jincheng", "朔州": "Shuozhou", "晋中": "Jinzhong", "运城": "Yuncheng",
        "忻州": "Xinzhou", "临汾": "Linfen", "吕梁": "Lüliang",
        "呼和浩特": "Hohhot", "包头": "Baotou", "乌海": "Wuhai",
        "赤峰": "Chifeng", "通辽": "Tongliao", "鄂尔多斯": "Ordos",
        "呼伦贝尔": "Hulunbuir", "巴彦淖尔": "Bayannur", "乌兰察布": "Ulanqab",
        "沈阳": "Shenyang", "大连": "Dalian", "鞍山": "Anshan", "抚顺": "Fushun",
        "本溪": "Benxi", "丹东": "Dandong", "锦州": "Jinzhou", "营口": "Yingkou",
        "阜新": "Fuxin", "辽阳": "Liaoyang", "盘锦": "Panjin", "铁岭": "Tieling",
        "朝阳": "Chaoyang", "葫芦岛": "Huludao",
        "长春": "Changchun", "吉林": "Jilin", "四平": "Siping", "辽源": "Liaoyuan",
        "通化": "Tonghua", "白山": "Baishan", "松原": "Songyuan", "白城": "Baicheng",
        "哈尔滨": "Harbin", "齐齐哈尔": "Qiqihar", "鸡西": "Jixi",
        "鹤岗": "Hegang", "双鸭山": "Shuangyashan", "大庆": "Daqing",
        "伊春": "Yichun", "佳木斯": "Jiamusi", "七台河": "Qitaihe",
        "牡丹江": "Mudanjiang", "黑河": "Heihe", "绥化": "Suihua",
        "西安": "Xi'an", "铜川": "Tongchuan", "宝鸡": "Baoji", "咸阳": "Xianyang",
        "渭南": "Weinan", "延安": "Yan'an", "汉中": "Hanzhong", "榆林": "Yulin",
        "安康": "Ankang", "商洛": "Shangluo",
        "济南": "Jinan", "青岛": "Qingdao", "淄博": "Zibo", "枣庄": "Zaozhuang",
        "烟台": "Yantai", "潍坊": "Weifang", "济宁": "Jining", "泰安": "Tai'an",
        "威海": "Weihai", "日照": "Rizhao", "临沂": "Linyi", "德州": "Dezhou",
        "聊城": "Liaocheng", "滨州": "Binzhou", "菏泽": "Heze", "东营": "Dongying",
        "郑州": "Zhengzhou", "开封": "Kaifeng", "洛阳": "Luoyang", "平顶山": "Pingdingshan",
        "安阳": "Anyang", "鹤壁": "Hebi", "新乡": "Xinxiang", "焦作": "Jiaozuo",
        "濮阳": "Puyang", "许昌": "Xuchang", "漯河": "Luohe", "三门峡": "Sanmenxia",
        "南阳": "Nanyang", "商丘": "Shangqiu", "信阳": "Xinyang", "周口": "Zhoukou",
        "驻马店": "Zhumadian",
        "武汉": "Wuhan", "黄石": "Huangshi", "十堰": "Shiyan",
        "宜昌": "Yichang", "襄阳": "Xiangyang", "鄂州": "Ezhou",
        "荆门": "Jingmen", "孝感": "Xiaogan", "荆州": "Jingzhou",
        "黄冈": "Huanggang", "咸宁": "Xianning", "随州": "Suizhou",
        "长沙": "Changsha", "株洲": "Zhuzhou", "湘潭": "Xiangtan", "衡阳": "Hengyang",
        "邵阳": "Shaoyang", "岳阳": "Yueyang", "常德": "Changde", "张家界": "Zhangjiajie",
        "益阳": "Yiyang", "郴州": "Chenzhou", "永州": "Yongzhou", "怀化": "Huaihua",
        "娄底": "Loudi",
        "广州": "Guangzhou", "韶关": "Shaoguan", "深圳": "Shenzhen", "珠海": "Zhuhai",
        "汕头": "Shantou", "佛山": "Foshan", "江门": "Jiangmen", "湛江": "Zhanjiang",
        "茂名": "Maoming", "肇庆": "Zhaoqing", "惠州": "Huizhou", "梅州": "Meizhou",
        "汕尾": "Shanwei", "河源": "Heyuan", "阳江": "Yangjiang", "清远": "Qingyuan",
        "东莞": "Dongguan", "中山": "Zhongshan", "潮州": "Chaozhou", "揭阳": "Jieyang",
        "云浮": "Yunfu",
        "南宁": "Nanning", "柳州": "Liuzhou", "桂林": "Guilin", "梧州": "Wuzhou",
        "北海": "Beihai", "防城港": "Fangchenggang", "钦州": "Qinzhou", "贵港": "Guigang",
        "玉林": "Yulin", "百色": "Baise", "贺州": "Hezhou", "河池": "Hechi",
        "来宾": "Laibin", "崇左": "Chongzuo",
        "海口": "Haikou", "三亚": "Sanya", "儋州": "Danzhou",
        "成都": "Chengdu", "自贡": "Zigong", "攀枝花": "Panzhihua", "泸州": "Luzhou",
        "德阳": "Deyang", "绵阳": "Mianyang", "广元": "Guangyuan", "遂宁": "Suining",
        "内江": "Neijiang", "乐山": "Leshan", "南充": "Nanchong", "眉山": "Meishan",
        "宜宾": "Yibin", "广安": "Guang'an", "达州": "Dazhou", "雅安": "Ya'an",
        "巴中": "Bazhong", "资阳": "Ziyang",
        "贵阳": "Guiyang", "六盘水": "Liupanshui", "遵义": "Zunyi", "安顺": "Anshun",
        "铜仁": "Tongren", "毕节": "Bijie",
        "昆明": "Kunming", "曲靖": "Qujing", "玉溪": "Yuxi", "保山": "Baoshan",
        "昭通": "Zhaotong", "丽江": "Lijiang", "普洱": "Pu'er", "临沧": "Lincang",
        "大理": "Dali",
        "拉萨": "Lhasa", "日喀则": "Shigatse", "昌都": "Chamdo",
        "林芝": "Nyingchi", "山南": "Shannan", "那曲": "Nagqu",
        "兰州": "Lanzhou", "嘉峪关": "Jiayuguan", "金昌": "Jinchang", "白银": "Baiyin",
        "天水": "Tianshui", "武威": "Wuwei", "张掖": "Zhangye", "平凉": "Pingliang",
        "酒泉": "Jiuquan", "庆阳": "Qingyang", "定西": "Dingxi", "陇南": "Longnan",
        "银川": "Yinchuan", "石嘴山": "Shizuishan", "吴忠": "Wuzhong",
        "固原": "Guyuan", "中卫": "Zhongwei",
        "西宁": "Xining", "海东": "Haidong",
        "乌鲁木齐": "Ürümqi", "克拉玛依": "Karamay", "吐鲁番": "Turpan",
        "哈密": "Hami", "昌吉": "Changji", "库尔勒": "Korla",
        "阿克苏": "Aksu", "喀什": "Kashgar",
        "远程": "Remote", "海外": "Overseas",
    }

    def build_search_url(self, keyword: str, city_code: str) -> str:
        # city_code 在这里是英文城市名
        location = city_code if city_code else ""
        return f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}"

    async def check_login(self, page) -> bool:
        # 跳过登录检查，直接搜索
        return True

    async def extract_jobs(self, page, limit: int) -> List[Dict]:
        """LinkedIn DOM 抓取。"""
        # 隐藏登录弹窗（CSS 隐藏比点击 dismiss 更可靠）
        try:
            await page.evaluate("""() => {
                for (const sel of ['.contextual-sign-in-modal', '.modal__overlay', '.modal__wrapper']) {
                    for (const el of document.querySelectorAll(sel)) {
                        el.style.display = 'none';
                    }
                }
            }""")
            await page.wait_for_timeout(300)
        except Exception:
            pass

        try:
            await page.wait_for_selector(".jobs-search__results-list li, .scaffold-layout__list", timeout=15000)
        except Exception:
            logger.warning("LinkedIn: job list selector not found")
            return []

        data = await page.evaluate("""
            (limit) => {
                let items = document.querySelectorAll('.jobs-search__results-list li, .scaffold-layout__list > *');
                const results = [];
                for (let i = 0; i < Math.min(items.length, limit); i++) {
                    const item = items[i];
                    const titleEl = item.querySelector('.base-card__full-link, .artdeco-entity-lockup__title a, .job-card-list__link');
                    const title = titleEl ? titleEl.textContent.trim() : '';
                    const href = titleEl ? titleEl.href : '';
                    const companyEl = item.querySelector('.base-search-card__subtitle, .artdeco-entity-lockup__subtitle, .job-card-container__primary-description');
                    const company = companyEl ? companyEl.textContent.trim() : '';
                    const locationEl = item.querySelector('.job-search-card__location, .artdeco-entity-lockup__caption, .job-card-container__metadata-item');
                    const location = locationEl ? locationEl.textContent.trim() : '';
                    const salaryEl = item.querySelector('.salary, .job-card-container__salary-info, [class*=salary]');
                    const salary = salaryEl ? salaryEl.textContent.trim() : '';
                    const tagEls = item.querySelectorAll('.job-card-container__skills-item, .job-card-container__job-insight');
                    const tags = Array.from(tagEls).map(e => e.textContent.trim());

                    if (title) {
                        results.push({title, salary, tags, company, location, href});
                    }
                }
                return results;
            }
        """, limit)

        results = []
        for item in data:
            title = item.get("title", "")
            company = item.get("company", "")
            city = item.get("location", "")
            salary = item.get("salary", "")
            tags = item.get("tags", [])
            href = item.get("href", "")

            raw = f"{title}\n{company}\n{city}\n{salary}"
            if tags:
                raw += f"\n技能：{' '.join(tags[:5])}"

            results.append({
                "platform": "linkedin",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })

        logger.info("LinkedIn: extracted %d jobs from DOM", len(results))
        return results
