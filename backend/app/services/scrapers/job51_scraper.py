from __future__ import annotations

import json as _json
import logging
import time
from typing import Dict, List
from urllib.parse import urlparse, parse_qs, urlencode

from app.services.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class Job51Scraper(BaseScraper):
    platform_id = "51job"
    label = "前程无忧"

    city_codes: Dict[str, str] = {
        "全国": "",
        "北京": "010000", "上海": "020000", "天津": "030000", "重庆": "040000",
        "石家庄": "050000", "唐山": "050500", "秦皇岛": "050600", "邯郸": "050700",
        "邢台": "050800", "保定": "050900", "张家口": "051000", "承德": "051100",
        "沧州": "051200", "廊坊": "051300", "衡水": "051400",
        "太原": "060000", "大同": "060100", "阳泉": "060200", "长治": "060300",
        "晋城": "060400", "朔州": "060500", "晋中": "060600", "运城": "060700",
        "忻州": "060800", "临汾": "060900", "吕梁": "061000",
        "呼和浩特": "070000", "包头": "070100", "乌海": "070200",
        "赤峰": "070300", "通辽": "070400", "鄂尔多斯": "070500",
        "呼伦贝尔": "070600", "巴彦淖尔": "070700", "乌兰察布": "070800",
        "沈阳": "080000", "大连": "080100", "鞍山": "080200", "抚顺": "080300",
        "本溪": "080400", "丹东": "080500", "锦州": "080600", "营口": "080700",
        "阜新": "080800", "辽阳": "080900", "盘锦": "081000", "铁岭": "081100",
        "朝阳": "081200", "葫芦岛": "081300",
        "长春": "090000", "吉林": "090100", "四平": "090200", "辽源": "090300",
        "通化": "090400", "白山": "090500", "松原": "090600", "白城": "090700",
        "哈尔滨": "100000", "齐齐哈尔": "100100", "鸡西": "100200",
        "鹤岗": "100300", "双鸭山": "100400", "大庆": "100500",
        "伊春": "100600", "佳木斯": "100700", "七台河": "100800",
        "牡丹江": "100900", "黑河": "101000", "绥化": "101100",
        "南京": "110000", "无锡": "110100", "徐州": "110200", "常州": "110300",
        "苏州": "110400", "南通": "110500", "连云港": "110600", "淮安": "110700",
        "盐城": "110800", "扬州": "110900", "镇江": "111000", "泰州": "111100",
        "宿迁": "111200",
        "杭州": "120000", "宁波": "120100", "温州": "120200", "嘉兴": "120300",
        "湖州": "120400", "绍兴": "120500", "金华": "120600", "衢州": "120700",
        "舟山": "120800", "台州": "120900", "丽水": "121000",
        "合肥": "130000", "芜湖": "130100", "蚌埠": "130200", "淮南": "130300",
        "马鞍山": "130400", "淮北": "130500", "铜陵": "130600", "安庆": "130700",
        "黄山": "130800", "滁州": "130900", "阜阳": "131000", "宿州": "131100",
        "六安": "131200", "亳州": "131300", "池州": "131400", "宣城": "131500",
        "福州": "140000", "厦门": "140100", "莆田": "140200", "三明": "140300",
        "泉州": "140400", "漳州": "140500", "南平": "140600", "龙岩": "140700",
        "宁德": "140800",
        "南昌": "150000", "景德镇": "150100", "萍乡": "150200", "九江": "150300",
        "新余": "150400", "鹰潭": "150500", "赣州": "150600", "吉安": "150700",
        "宜春": "150800", "抚州": "150900", "上饶": "151000",
        "济南": "160000", "青岛": "160100", "淄博": "160200", "枣庄": "160300",
        "烟台": "160400", "潍坊": "160500", "济宁": "160600", "泰安": "160700",
        "威海": "160800", "日照": "160900", "临沂": "161000", "德州": "161100",
        "聊城": "161200", "滨州": "161300", "菏泽": "161400", "东营": "161500",
        "郑州": "170000", "开封": "170100", "洛阳": "170200", "平顶山": "170300",
        "安阳": "170400", "鹤壁": "170500", "新乡": "170600", "焦作": "170700",
        "濮阳": "170800", "许昌": "170900", "漯河": "171000", "三门峡": "171100",
        "南阳": "171200", "商丘": "171300", "信阳": "171400", "周口": "171500",
        "驻马店": "171600",
        "武汉": "180000", "黄石": "180100", "十堰": "180200",
        "宜昌": "180300", "襄阳": "180400", "鄂州": "180500",
        "荆门": "180600", "孝感": "180700", "荆州": "180800",
        "黄冈": "180900", "咸宁": "181000", "随州": "181100",
        "长沙": "190000", "株洲": "190100", "湘潭": "190200", "衡阳": "190300",
        "邵阳": "190400", "岳阳": "190500", "常德": "190600", "张家界": "190700",
        "益阳": "190800", "郴州": "190900", "永州": "191000", "怀化": "191100",
        "娄底": "191200",
        "广州": "200000", "韶关": "200100", "深圳": "200200", "珠海": "200300",
        "汕头": "200400", "佛山": "200500", "江门": "200600", "湛江": "200700",
        "茂名": "200800", "肇庆": "200900", "惠州": "201000", "梅州": "201100",
        "汕尾": "201200", "河源": "201300", "阳江": "201400", "清远": "201500",
        "东莞": "201600", "中山": "201700", "潮州": "201800", "揭阳": "201900",
        "云浮": "202000",
        "南宁": "210000", "柳州": "210100", "桂林": "210200", "梧州": "210300",
        "北海": "210400", "防城港": "210500", "钦州": "210600", "贵港": "210700",
        "玉林": "210800", "百色": "210900", "贺州": "211000", "河池": "211100",
        "来宾": "211200", "崇左": "211300",
        "海口": "220000", "三亚": "220100", "儋州": "220200",
        "成都": "230000", "自贡": "230100", "攀枝花": "230200", "泸州": "230300",
        "德阳": "230400", "绵阳": "230500", "广元": "230600", "遂宁": "230700",
        "内江": "230800", "乐山": "230900", "南充": "231000", "眉山": "231100",
        "宜宾": "231200", "广安": "231300", "达州": "231400", "雅安": "231500",
        "巴中": "231600", "资阳": "231700",
        "贵阳": "240000", "六盘水": "240100", "遵义": "240200", "安顺": "240300",
        "铜仁": "240400", "毕节": "240500",
        "昆明": "250000", "曲靖": "250100", "玉溪": "250200", "保山": "250300",
        "昭通": "250400", "丽江": "250500", "普洱": "250600", "临沧": "250700",
        "大理": "250800",
        "西安": "260000", "铜川": "260100", "宝鸡": "260200", "咸阳": "260300",
        "渭南": "260400", "延安": "260500", "汉中": "260600", "榆林": "260700",
        "安康": "260800", "商洛": "260900",
        "兰州": "270000", "嘉峪关": "270100", "金昌": "270200", "白银": "270300",
        "天水": "270400", "武威": "270500", "张掖": "270600", "平凉": "270700",
        "酒泉": "270800", "庆阳": "270900", "定西": "271000", "陇南": "271100",
        "银川": "280000", "石嘴山": "280100", "吴忠": "280200",
        "固原": "280300", "中卫": "280400",
        "西宁": "290000", "海东": "290100",
        "乌鲁木齐": "300000", "克拉玛依": "300100", "吐鲁番": "300200",
        "哈密": "300300", "昌吉": "300400", "库尔勒": "300500",
        "阿克苏": "300600", "喀什": "300700",
        "拉萨": "310000", "日喀则": "310100", "昌都": "310200",
        "林芝": "310300", "山南": "310400", "那曲": "310500",
    }

    def build_search_url(self, keyword: str, city_code: str) -> str:
        # 不传城市代码，完全依赖 UI 城市筛选（避免自动选中其他城市）
        return f"https://we.51job.com/pc/search?keyword={keyword}&searchType=2"

    async def check_login(self, page) -> bool:
        try:
            body_text = await page.evaluate('document.body.innerText.substring(0, 3000)')
            if "我的51job" in body_text or "退出" in body_text:
                return True
            if "登录" in body_text and "注册" in body_text:
                return False
            return True
        except Exception:
            return True

    async def on_response(self, response, captured_data: list):
        """拦截 search-pc API 响应。"""
        if "search-pc" not in response.url or response.status != 200:
            return
        try:
            raw = await response.body()
            text = raw.decode("utf-8", errors="replace")
            if not text or len(text) < 10:
                return
            body = _json.loads(text)
            if str(body.get("status")) != "1":
                return
            job = (body.get("resultbody") or {}).get("job") or {}
            items = job.get("items", [])
            if items:
                captured_data.extend(items)
        except Exception as exc:
            logger.debug("[51job] API parse err: %s", exc)

    async def extract_jobs(self, page, limit: int, city: str = "") -> List[Dict]:
        """从 API 拦截数据或 DOM 提取职位。"""
        if hasattr(self, "_captured_data") and self._captured_data:
            results = self._parse_api_jobs(self._captured_data)
            # 按城市名过滤，排除异地招聘
            if city:
                filtered = [r for r in results if city in r.get("city", "")]
                if filtered:
                    logger.info("[51job] filtered %d/%d items for city '%s'", len(filtered), len(results), city)
                    return filtered[:limit]
                # 城市筛选已应用但无匹配 = 该城市确实没有匹配的职位
                logger.info("[51job] city '%s' has 0 matching jobs, returning empty", city)
                return []
            return results[:limit]

        # Fallback: DOM 抓取
        return await self._extract_jobs_dom(page, limit)

    def _parse_api_jobs(self, items: list) -> List[Dict]:
        """解析 API 拦截的职位数据。"""
        results = []
        for item in items:
            title = item.get("jobName", "")
            company = item.get("companyName", "") or item.get("fullCompanyName", "")
            salary = item.get("provideSalaryString", "")
            city = item.get("jobAreaString", "")
            experience = item.get("workYearString", "")
            education = item.get("degreeString", "")
            href = item.get("jobHref", "")
            tags = item.get("jobTags", [])
            if isinstance(tags, list):
                tags = [t.get("jobTagName", t) if isinstance(t, dict) else str(t) for t in tags]

            raw = f"{title}\n{company}\n{city}\n{salary}"
            if experience:
                raw += f"\n经验：{experience}"
            if education:
                raw += f"\n学历：{education}"
            if tags:
                raw += f"\n技能：{' '.join(tags[:5])}"

            results.append({
                "platform": "51job",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })
        return results

    async def _extract_jobs_dom(self, page, limit: int) -> List[Dict]:
        """DOM 抓取（API 拦截失败时的 fallback）。"""
        try:
            await page.wait_for_selector(".job-item, .joblist-box__item, .j_joblist .e", timeout=15000)
        except Exception:
            logger.warning("[51job] DOM: 职位列表未找到")
            return []

        data = await page.evaluate("""
            (limit) => {
                let items = document.querySelectorAll('.job-item');
                if (items.length === 0) items = document.querySelectorAll('.joblist-box__item');
                if (items.length === 0) items = document.querySelectorAll('.j_joblist .e');
                const results = [];
                for (let i = 0; i < Math.min(items.length, limit); i++) {
                    const item = items[i];
                    let titleEl = item.querySelector('.job-name, .jobinfo__name, .jname, .name a');
                    let title = titleEl ? titleEl.textContent.trim() : '';
                    let href = (titleEl && titleEl.closest('a')) ? titleEl.closest('a').href : (titleEl && titleEl.href) ? titleEl.href : '';
                    let salaryEl = item.querySelector('.salary, .jobinfo__salary, .sal');
                    let salary = salaryEl ? salaryEl.textContent.trim() : '';
                    let companyEl = item.querySelector('.company, .companyinfo__name, .cname');
                    let company = companyEl ? companyEl.textContent.trim() : '';
                    let locationEl = item.querySelector('.location');
                    let city = locationEl ? locationEl.textContent.trim() : '';
                    if (title) results.push({title, salary, company, city, href});
                }
                return results;
            }
        """, limit)

        results = []
        for item in data:
            title = item.get("title", "")
            company = item.get("company", "")
            salary = item.get("salary", "")
            city = item.get("city", "")
            href = item.get("href", "")

            raw = f"{title}\n{company}\n{city}\n{salary}"
            results.append({
                "platform": "51job",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })

        logger.info("[51job] DOM 提取 %d 条结果", len(results))
        return results

    @staticmethod
    def _get_pinyin_initial(char: str) -> str:
        """获取中文字符的拼音首字母（用于51job字母索引）。"""
        _MAP = {
            "阿": "A", "埃": "A", "安": "A", "傲": "A", "奥": "A",
            "八": "B", "白": "B", "百": "B", "班": "B", "包": "B",
            "保": "B", "北": "B", "本": "B", "毕": "B", "滨": "B",
            "冰": "B", "并": "B", "博": "B", "渤": "B", "补": "B",
            "布": "B", "才": "C", "参": "C", "苍": "C", "藏": "C",
            "曹": "C", "册": "C", "策": "C", "层": "C", "查": "C",
            "察": "C", "昌": "C", "长": "C", "常": "C", "朝": "C",
            "陈": "C", "成": "C", "城": "C", "程": "C", "池": "C",
            "赤": "C", "充": "C", "崇": "C", "滁": "C", "楚": "C",
            "川": "C", "传": "C", "创": "C", "春": "C", "慈": "C",
            "次": "C", "从": "C", "村": "C", "达": "D", "大": "D",
            "丹": "D", "但": "D", "德": "D", "登": "D", "迪": "D",
            "电": "D", "定": "D", "东": "D", "都": "D", "斗": "D",
            "杜": "D", "端": "D", "堆": "D", "顿": "D", "多": "D",
            "额": "E", "恩": "E", "尔": "E", "二": "E", "发": "F",
            "繁": "F", "范": "F", "方": "F", "坊": "F", "防": "F",
            "飞": "F", "费": "F", "分": "F", "丰": "F", "风": "F",
            "峰": "F", "凤": "F", "奉": "F", "福": "F", "阜": "F",
            "复": "F", "富": "F", "改": "G", "甘": "G", "赣": "G",
            "高": "G", "告": "G", "格": "G", "各": "G", "根": "G",
            "更": "G", "工": "G", "公": "G", "功": "G", "共": "G",
            "狗": "G", "古": "G", "谷": "G", "固": "G", "关": "G",
            "观": "G", "管": "G", "广": "G", "贵": "G", "桂": "G",
            "国": "G", "果": "G", "过": "G", "哈": "H", "海": "H",
            "韩": "H", "汉": "H", "杭": "H", "豪": "H", "好": "H",
            "合": "H", "河": "H", "贺": "H", "黑": "H", "很": "H",
            "恒": "H", "衡": "H", "红": "H", "洪": "H", "后": "H",
            "呼": "H", "湖": "H", "虎": "H", "互": "H", "花": "H",
            "华": "H", "化": "H", "怀": "H", "环": "H", "黄": "H",
            "回": "H", "会": "H", "惠": "H", "婚": "H", "活": "H",
            "火": "H", "霍": "H", "基": "J", "极": "J", "吉": "J",
            "集": "J", "几": "J", "济": "J", "暨": "J", "加": "J",
            "佳": "J", "家": "J", "嘉": "J", "坚": "J", "间": "J",
            "建": "J", "江": "J", "姜": "J", "将": "J", "交": "J",
            "角": "J", "脚": "J", "缴": "J", "叫": "J", "揭": "J",
            "节": "J", "杰": "J", "金": "J", "津": "J", "进": "J",
            "晋": "J", "京": "J", "经": "J", "精": "J", "井": "J",
            "景": "J", "靖": "J", "九": "J", "酒": "J", "旧": "J",
            "居": "J", "军": "J", "均": "J", "开": "K", "凯": "K",
            "看": "K", "康": "K", "考": "K", "科": "K", "可": "K",
            "克": "K", "空": "K", "孔": "K", "口": "K", "库": "K",
            "快": "K", "宽": "K", "况": "K", "昆": "K", "拉": "L",
            "来": "L", "兰": "L", "蓝": "L", "朗": "L", "乐": "L",
            "雷": "L", "冷": "L", "梨": "L", "黎": "L", "李": "L",
            "里": "L", "理": "L", "力": "L", "历": "L", "丽": "L",
            "利": "L", "连": "L", "莲": "L", "廉": "L", "良": "L",
            "梁": "L", "两": "L", "辽": "L", "林": "L", "临": "L",
            "凌": "L", "灵": "L", "领": "L", "令": "L", "龙": "L",
            "陇": "L", "楼": "L", "卢": "L", "泸": "L", "鲁": "L",
            "陆": "L", "录": "L", "鹿": "L", "路": "L", "洛": "L",
            "络": "L", "旅": "L", "绿": "L", "妈": "M", "马": "M",
            "玛": "M", "满": "M", "芒": "M", "忙": "M", "毛": "M",
            "么": "M", "没": "M", "梅": "M", "美": "M", "门": "M",
            "蒙": "M", "孟": "M", "米": "M", "密": "M", "免": "M",
            "面": "M", "民": "M", "明": "M", "鸣": "M", "命": "M",
            "模": "M", "莫": "M", "墨": "M", "默": "M", "谋": "M",
            "木": "M", "目": "M", "牧": "M", "南": "N", "内": "N",
            "能": "M", "尼": "N", "你": "N", "年": "N", "宁": "N",
            "农": "N", "努": "N", "女": "N", "欧": "O", "盘": "P",
            "旁": "P", "跑": "P", "配": "P", "朋": "P", "批": "P",
            "皮": "P", "漂": "P", "平": "P", "评": "P", "凭": "P",
            "莆": "P", "浦": "P", "普": "P", "七": "Q", "齐": "Q",
            "其": "Q", "奇": "Q", "骑": "Q", "启": "Q", "气": "Q",
            "千": "Q", "前": "Q", "黔": "Q", "强": "Q", "桥": "Q",
            "秦": "Q", "青": "Q", "轻": "Q", "庆": "Q", "穷": "Q",
            "丘": "Q", "秋": "Q", "区": "Q", "曲": "Q", "屈": "Q",
            "全": "Q", "泉": "Q", "群": "Q", "然": "R", "让": "R",
            "热": "R", "人": "R", "日": "R", "容": "R", "如": "R",
            "入": "R", "三": "S", "桑": "S", "色": "S", "沙": "S",
            "山": "S", "汕": "S", "商": "S", "上": "S", "韶": "S",
            "少": "S", "绍": "S", "社": "S", "深": "S", "沈": "S",
            "升": "S", "生": "S", "省": "S", "圣": "S", "师": "S",
            "十": "S", "石": "S", "时": "S", "实": "S", "史": "S",
            "始": "S", "世": "S", "市": "S", "试": "S", "收": "S",
            "手": "S", "首": "S", "寿": "S", "书": "S", "蜀": "S",
            "术": "S", "树": "S", "双": "S", "水": "S", "顺": "S",
            "司": "S", "思": "S", "四": "S", "松": "S", "苏": "S",
            "宿": "S", "绥": "S", "碎": "S", "遂": "S", "孙": "S",
            "台": "T", "太": "T", "泰": "T", "唐": "T", "桃": "T",
            "特": "T", "天": "T", "田": "T", "铁": "T", "通": "T",
            "同": "T", "铜": "T", "头": "T", "图": "T", "土": "T",
            "团": "T", "屯": "T", "陀": "T", "万": "W", "汪": "W",
            "王": "W", "望": "W", "威": "W", "微": "W", "为": "W",
            "维": "W", "卫": "W", "温": "W", "文": "W", "闻": "W",
            "翁": "W", "乌": "W", "无": "W", "武": "W", "务": "W",
            "西": "X", "希": "X", "息": "X", "习": "X", "喜": "X",
            "下": "X", "夏": "X", "先": "X", "仙": "X", "咸": "X",
            "湘": "X", "乡": "X", "襄": "X", "祥": "X", "小": "X",
            "孝": "X", "校": "X", "协": "X", "新": "X", "信": "X",
            "星": "X", "兴": "X", "行": "X", "邢": "X", "雄": "X",
            "休": "X", "徐": "X", "许": "X", "宣": "X", "玄": "X",
            "雪": "X", "循": "X", "牙": "Y", "雅": "Y", "亚": "Y",
            "延": "Y", "言": "Y", "盐": "Y", "阳": "Y", "杨": "Y",
            "洋": "Y", "姚": "Y", "药": "Y", "叶": "Y", "一": "Y",
            "伊": "Y", "银": "Y", "应": "Y", "英": "Y", "营": "Y",
            "永": "Y", "友": "Y", "有": "Y", "右": "Y", "余": "Y",
            "鱼": "Y", "渝": "Y", "玉": "Y", "域": "Y", "元": "Y",
            "原": "Y", "远": "Y", "月": "Y", "云": "Y", "运": "Y",
            "再": "Z", "在": "Z", "泽": "Z", "曾": "Z", "扎": "Z",
            "张": "Z", "章": "Z", "长": "Z", "兆": "Z", "赵": "Z",
            "这": "Z", "浙": "Z", "镇": "Z", "正": "Z", "郑": "Z",
            "之": "Z", "支": "Z", "芝": "Z", "枝": "Z", "直": "Z",
            "指": "Z", "中": "Z", "钟": "Z", "重": "Z", "州": "Z",
            "舟": "Z", "珠": "Z", "竹": "Z", "主": "Z", "注": "Z",
            "驻": "Z", "柱": "Z", "资": "Z", "自": "Z", "字": "Z",
            "宗": "Z", "总": "Z", "组": "Z", "遵": "Z", "左": "Z",
        }
        if char in _MAP:
            return _MAP[char]
        if char.isascii() and char.isalpha():
            return char.upper()
        return "A"

    async def _click_confirm(self, page):
        """关闭城市选择弹窗：优先点击确定按钮，否则按 Escape。"""
        try:
            confirm_btn = await page.query_selector('span.dialog_footer_wrapper')
            if confirm_btn:
                await confirm_btn.click()
                await page.wait_for_timeout(1500)
                return

            confirm_clicked = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button, a, span, div');
                    for (const btn of btns) {
                        const text = btn.textContent.trim();
                        const rect = btn.getBoundingClientRect();
                        if (text === '确定' && rect.width > 0 && rect.height > 0
                            && rect.width < 200 && rect.height < 80) {
                            const child = btn.querySelector('span, a, button') || btn;
                            child.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if confirm_clicked:
                await page.wait_for_timeout(1500)
                return

            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1500)
        except Exception as exc:
            logger.warning("[51job] close city dialog failed: %s", exc)

    async def _force_research(self, page, keyword: str):
        """触发重新搜索：点击搜索按钮 → 清空输入框重新输入 → 按回车。"""
        try:
            btn_clicked = await page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button, a, span, div');
                    for (const btn of btns) {
                        const text = btn.textContent.trim();
                        const rect = btn.getBoundingClientRect();
                        if (text === '搜索' && rect.width > 20 && rect.height > 20
                            && rect.top > 0 && rect.top < 200) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if btn_clicked:
                await page.wait_for_timeout(5000)
                return

            search_input = await page.query_selector('input[type="text"], input.search-input, input[placeholder*="搜索"]')
            if search_input:
                await search_input.click()
                await page.wait_for_timeout(300)
                await search_input.fill("")
                await page.wait_for_timeout(300)
                await search_input.type(keyword, delay=50)
                await page.wait_for_timeout(500)
                await search_input.press("Enter")
                await page.wait_for_timeout(5000)
        except Exception as exc:
            logger.debug("[51job] _force_research failed: %s", exc)

    async def _select_landmark(self, page, city: str) -> bool:
        """选择地区地标：优先点"城市名市"，没有则点"全部"。返回是否点击了地标。"""
        try:
            await page.wait_for_timeout(2000)

            has_landmark = await page.evaluate("""
                () => {
                    const allEls = document.querySelectorAll('*');
                    for (const el of allEls) {
                        if (el.textContent.trim() === '地区地标' && el.getBoundingClientRect().width > 0) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if not has_landmark:
                return False

            city_with_suffix = city + "市"
            clicked = await page.evaluate("""
                (opts) => {
                    const cityName = opts.cityName;
                    const citySuffix = opts.citySuffix;
                    const allEls = document.querySelectorAll('a, span, div, li');
                    for (const el of allEls) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text === citySuffix && rect.width > 0 && rect.height > 0
                            && rect.top > 100 && rect.top < 500) {
                            el.click();
                            return true;
                        }
                    }
                    for (const el of allEls) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text === cityName && rect.width > 0 && rect.height > 0
                            && rect.top > 100 && rect.top < 500 && text.length >= 2) {
                            el.click();
                            return true;
                        }
                    }
                    for (const el of allEls) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text === '全部' && rect.width > 0 && rect.height > 0
                            && rect.top > 100 && rect.top < 500) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """, {"cityName": city, "citySuffix": city_with_suffix})

            if clicked:
                await page.wait_for_timeout(1500)
                return True
            return False
        except Exception as exc:
            logger.debug("[51job] landmark selection failed: %s", exc)
            return False

    async def apply_city_filter(self, page, city: str) -> bool:
        """前程无忧 UI 城市筛选。最小化 evaluate 调用和等待时间。"""
        try:
            logger.info("[51job] applying city filter: %s", city)

            first_letter = self._get_pinyin_initial(city[0])

            # Evaluate 1: 查找工作地点行 → 点击"其他城市"
            result = await page.evaluate("""
                (params) => {
                    const cityName = params.cityName;
                    const allEls = document.querySelectorAll('*');

                    // 在"工作地点"行查找城市
                    for (const el of allEls) {
                        if (el.childNodes.length === 1 && el.textContent.trim() === '工作地点') {
                            const section = el.parentElement || el;
                            const links = section.querySelectorAll('a, span, div, li');
                            for (const link of links) {
                                if (link.textContent.trim() === cityName && link.getBoundingClientRect().width > 0) {
                                    link.click();
                                    return 'workarea';
                                }
                            }
                            break;
                        }
                    }

                    // 点击"其他城市"
                    for (const el of allEls) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text === '其他城市' && rect.width > 0 && rect.top > 200 && rect.top < 400) {
                            el.click();
                            return 'other_cities';
                        }
                    }
                    return false;
                }
            """, {"cityName": city, "letter": first_letter})

            if result == "workarea":
                logger.info("[51job] clicked work area: %s", city)
                await page.wait_for_timeout(1000)
                return True

            if result != "other_cities":
                logger.warning("[51job] city '%s' not in work area or other cities", city)
                return False

            logger.info("[51job] city '%s' not in work area, opening city selector", city)
            await page.wait_for_timeout(1000)

            # 点击"全部城市"进入完整城市列表（含字母索引）
            # 使用 evaluate 点击以绕过弹窗遮挡
            allcity_clicked = await page.evaluate("""
                () => {
                    const el = document.querySelector('.allcity');
                    if (el) { el.click(); return true; }
                    return false;
                }
            """)
            if allcity_clicked:
                logger.info("[51job] clicked .allcity")
                await page.wait_for_timeout(1500)
            else:
                logger.warning("[51job] .allcity not found")

            # Evaluate 2: 全部城市页面中的字母索引
            clicked = await page.evaluate("""
                (params) => {
                    const letter = params.letter;
                    const allEls = document.querySelectorAll('*');

                    // 找字母索引按钮（单个大写字母）
                    for (const el of allEls) {
                        const t = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (t === letter && rect.width > 0 && rect.height > 0
                            && rect.top > 100 && rect.width < 50) {
                            el.click();
                            return 'letter';
                        }
                    }

                    // 备选：找包含"按字母选择"的容器
                    for (const el of allEls) {
                        const t = el.textContent.trim();
                        if (t.includes('按字母') && el.getBoundingClientRect().width > 0) {
                            const container = (el.parentElement || el).parentElement || el;
                            const btns = container.querySelectorAll('a, span, div, p');
                            for (const btn of btns) {
                                if (btn.textContent.trim() === letter && btn.getBoundingClientRect().width > 0) {
                                    btn.click();
                                    return 'letter';
                                }
                            }
                            break;
                        }
                    }
                    return false;
                }
            """, {"cityName": city, "letter": first_letter})

            if clicked != "letter":
                logger.warning("[51job] letter '%s' not found in city list", first_letter)
                return False

            logger.info("[51job] clicked letter: %s", first_letter)
            await page.wait_for_timeout(500)

            # Evaluate 3: 字母展开后点击目标城市
            city_clicked = await page.evaluate("""
                (cityName) => {
                    const allEls = document.querySelectorAll('*');
                    for (const el of allEls) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text.length === 1 && /[A-Z]/.test(text) && rect.width > 0 && rect.height > 0) {
                            const parent = el.parentElement || el;
                            const siblings = parent.querySelectorAll('a, span, div, li');
                            for (const sib of siblings) {
                                if (sib.textContent.trim() === cityName && sib.getBoundingClientRect().width > 0) {
                                    sib.click();
                                    return true;
                                }
                            }
                        }
                    }
                    const clickables = document.querySelectorAll('a, span, li');
                    for (const el of clickables) {
                        const text = el.textContent.trim();
                        const rect = el.getBoundingClientRect();
                        if (text === cityName && rect.width > 0 && rect.height > 0
                            && rect.top > 300 && rect.width < 200) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """, city)

            if city_clicked:
                logger.info("[51job] clicked city: %s", city)
                await self._click_confirm(page)
                return True
            else:
                logger.warning("[51job] city '%s' not found in list", city)

        except Exception as exc:
            logger.warning("[51job] city filter failed: %s", exc)
        return False

    async def scrape_search(
        self, context, keyword: str, city: str, limit: int = 5,
    ) -> List[Dict]:
        """前程无忧搜索：导航 → UI 城市筛选 → API 拦截。"""
        import time as _time
        _t0 = _time.time()
        city_code = self.get_city_code(city) if city else ""
        url = self.build_search_url(keyword, city_code)
        logger.info("[51job] city='%s' code='%s'", city, city_code)
        page = await context.new_page()
        self._captured_data: List[dict] = []

        async def _on_response(response):
            try:
                if response.status != 200:
                    return
                await self.on_response(response, self._captured_data)
            except Exception:
                pass

        page.on("response", _on_response)

        try:
            _t1 = _time.time()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info("[51job] timing: goto %.1fs", _time.time() - _t1)
            await page.bring_to_front()

            if city:
                await page.wait_for_timeout(1000)
                _t2 = _time.time()
                filter_ok = await self.apply_city_filter(page, city)
                logger.info("[51job] timing: city_filter %.1fs", _time.time() - _t2)
                for _ in range(8):
                    await page.wait_for_timeout(1000)
                    if self._captured_data:
                        break
                logger.info("[51job] captured %d API items after city filter", len(self._captured_data))
            else:
                for _ in range(5):
                    await page.wait_for_timeout(1500)
                    if self._captured_data:
                        break

            logger.info("[51job] timing: total %.1fs", _time.time() - _t0)

            if self._captured_data:
                return await self.extract_jobs(page, limit, city)

            # Fallback: DOM
            return await self._extract_jobs_dom(page, limit)
        except Exception as exc:
            logger.warning("[51job] error: %s", exc)
            if self._captured_data:
                return self._parse_api_jobs(self._captured_data)[:limit]
            return []
        finally:
            await page.close()
