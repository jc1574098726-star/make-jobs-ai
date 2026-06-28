from __future__ import annotations

import json as _json
import logging
from typing import Dict, List

from app.services.scrapers.base import BaseScraper

_PINYIN_MAP = {
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
    "古": "G", "谷": "G", "固": "G", "关": "G", "观": "G",
    "管": "G", "广": "G", "贵": "G", "桂": "G", "国": "G",
    "果": "G", "过": "G", "哈": "H", "海": "H", "韩": "H",
    "汉": "H", "杭": "H", "豪": "H", "好": "H", "合": "H",
    "河": "H", "贺": "H", "黑": "H", "很": "H", "恒": "H",
    "衡": "H", "红": "H", "洪": "H", "后": "H", "呼": "H",
    "湖": "H", "虎": "H", "互": "H", "花": "H", "华": "H",
    "化": "H", "怀": "H", "环": "H", "黄": "H", "回": "H",
    "会": "H", "惠": "H", "婚": "H", "活": "H", "火": "H",
    "霍": "H", "基": "J", "极": "J", "吉": "J", "集": "J",
    "几": "J", "济": "J", "暨": "J", "加": "J", "佳": "J",
    "家": "J", "嘉": "J", "坚": "J", "间": "J", "建": "J",
    "江": "J", "姜": "J", "将": "J", "交": "J", "角": "J",
    "脚": "J", "缴": "J", "叫": "J", "揭": "J", "节": "J",
    "杰": "J", "金": "J", "津": "J", "进": "J", "晋": "J",
    "京": "J", "经": "J", "精": "J", "井": "J", "景": "J",
    "靖": "J", "九": "J", "酒": "J", "旧": "J", "居": "J",
    "军": "J", "均": "J", "开": "K", "凯": "K", "看": "K",
    "康": "K", "考": "K", "科": "K", "可": "K", "克": "K",
    "空": "K", "孔": "K", "口": "K", "库": "K", "快": "K",
    "宽": "K", "况": "K", "昆": "K", "拉": "L", "来": "L",
    "兰": "L", "蓝": "L", "朗": "L", "乐": "L", "雷": "L",
    "冷": "L", "梨": "L", "黎": "L", "李": "L", "里": "L",
    "理": "L", "力": "L", "历": "L", "丽": "L", "利": "L",
    "连": "L", "莲": "L", "廉": "L", "良": "L", "梁": "L",
    "两": "L", "辽": "L", "林": "L", "临": "L", "凌": "L",
    "灵": "L", "领": "L", "令": "L", "龙": "L", "陇": "L",
    "楼": "L", "卢": "L", "泸": "L", "鲁": "L", "陆": "L",
    "录": "L", "鹿": "L", "路": "L", "洛": "L", "络": "L",
    "旅": "L", "绿": "L", "妈": "M", "马": "M", "玛": "M",
    "满": "M", "芒": "M", "忙": "M", "毛": "M", "么": "M",
    "没": "M", "梅": "M", "美": "M", "门": "M", "蒙": "M",
    "孟": "M", "米": "M", "密": "M", "免": "M", "面": "M",
    "民": "M", "明": "M", "鸣": "M", "命": "M", "模": "M",
    "莫": "M", "墨": "M", "默": "M", "谋": "M", "木": "M",
    "目": "M", "牧": "M", "南": "N", "内": "N", "能": "N",
    "尼": "N", "你": "N", "年": "N", "宁": "N", "农": "N",
    "努": "N", "女": "N", "欧": "O", "盘": "P", "旁": "P",
    "跑": "P", "配": "P", "朋": "P", "批": "P", "皮": "P",
    "漂": "P", "平": "P", "评": "P", "凭": "P", "莆": "P",
    "浦": "P", "普": "P", "七": "Q", "齐": "Q", "其": "Q",
    "奇": "Q", "骑": "Q", "启": "Q", "气": "Q", "千": "Q",
    "前": "Q", "黔": "Q", "强": "Q", "桥": "Q", "秦": "Q",
    "青": "Q", "轻": "Q", "庆": "Q", "穷": "Q", "丘": "Q",
    "秋": "Q", "区": "Q", "曲": "Q", "屈": "Q", "全": "Q",
    "泉": "Q", "群": "Q", "然": "R", "让": "R", "热": "R",
    "人": "R", "日": "R", "容": "R", "如": "R", "入": "R",
    "三": "S", "桑": "S", "色": "S", "沙": "S", "山": "S",
    "汕": "S", "商": "S", "上": "S", "韶": "S", "少": "S",
    "绍": "S", "社": "S", "深": "S", "沈": "S", "升": "S",
    "生": "S", "省": "S", "圣": "S", "师": "S", "十": "S",
    "石": "S", "时": "S", "实": "S", "史": "S", "始": "S",
    "世": "S", "市": "S", "试": "S", "收": "S", "手": "S",
    "首": "S", "寿": "S", "书": "S", "蜀": "S", "术": "S",
    "树": "S", "双": "S", "水": "S", "顺": "S", "司": "S",
    "思": "S", "四": "S", "松": "S", "苏": "S", "宿": "S",
    "绥": "S", "碎": "S", "遂": "S", "孙": "S", "台": "T",
    "太": "T", "泰": "T", "唐": "T", "桃": "T", "特": "T",
    "天": "T", "田": "T", "铁": "T", "通": "T", "同": "T",
    "铜": "T", "头": "T", "图": "T", "土": "T", "团": "T",
    "屯": "T", "陀": "T", "万": "W", "汪": "W", "王": "W",
    "望": "W", "威": "W", "微": "W", "为": "W", "维": "W",
    "卫": "W", "温": "W", "文": "W", "闻": "W", "翁": "W",
    "乌": "W", "无": "W", "武": "W", "务": "W", "西": "X",
    "希": "X", "息": "X", "习": "X", "喜": "X", "下": "X",
    "夏": "X", "先": "X", "仙": "X", "咸": "X", "湘": "X",
    "乡": "X", "襄": "X", "祥": "X", "小": "X", "孝": "X",
    "校": "X", "协": "X", "新": "X", "信": "X", "星": "X",
    "兴": "X", "行": "X", "邢": "X", "雄": "X", "休": "X",
    "徐": "X", "许": "X", "宣": "X", "玄": "X", "雪": "X",
    "循": "X", "牙": "Y", "雅": "Y", "亚": "Y", "延": "Y",
    "言": "Y", "盐": "Y", "阳": "Y", "杨": "Y", "洋": "Y",
    "姚": "Y", "药": "Y", "叶": "Y", "一": "Y", "伊": "Y",
    "银": "Y", "应": "Y", "英": "Y", "营": "Y", "永": "Y",
    "友": "Y", "有": "Y", "右": "Y", "余": "Y", "鱼": "Y",
    "渝": "Y", "玉": "Y", "域": "Y", "元": "Y", "原": "Y",
    "远": "Y", "月": "Y", "云": "Y", "运": "Y", "再": "Z",
    "在": "Z", "泽": "Z", "曾": "Z", "扎": "Z", "张": "Z",
    "章": "Z", "长": "Z", "兆": "Z", "赵": "Z", "这": "Z",
    "浙": "Z", "镇": "Z", "正": "Z", "郑": "Z", "之": "Z",
    "支": "Z", "芝": "Z", "枝": "Z", "直": "Z", "指": "Z",
    "中": "Z", "钟": "Z", "重": "Z", "州": "Z", "舟": "Z",
    "珠": "Z", "竹": "Z", "主": "Z", "注": "Z", "驻": "Z",
    "柱": "Z", "资": "Z", "自": "Z", "字": "Z", "宗": "Z",
    "总": "Z", "组": "Z", "遵": "Z", "左": "Z",
}

logger = logging.getLogger(__name__)


class YingjieshengScraper(BaseScraper):
    platform_id = "yingjiesheng"
    label = "应届生求职"
    route_patterns = ["**/youngapi.yingjiesheng.com/**", "**/vapi.51job.com/**"]
    use_persistent_context = False  # 避免持久化上下文导致卡死

    city_codes: Dict[str, str] = {
        "全国": "",
        # 直辖市
        "北京": "010000", "上海": "020000", "天津": "050000", "重庆": "060000",
        # 河北省
        "石家庄": "160200", "廊坊": "160300", "保定": "160400", "唐山": "160500", "秦皇岛": "160600", "邯郸": "160700", "衡水": "161200",
        # 山西省
        "太原": "210200", "运城": "210300", "大同": "210400", "临汾": "210500",
        # 内蒙古
        "呼和浩特": "280200", "赤峰": "280300", "包头": "280400", "鄂尔多斯": "280800",
        # 辽宁省
        "沈阳": "230200", "大连": "230300", "鞍山": "230400", "营口": "230500", "抚顺": "230600", "锦州": "230700", "丹东": "230800", "葫芦岛": "230900", "本溪": "231000", "辽阳": "231100", "铁岭": "231200", "阜新": "231500",
        # 吉林省
        "长春": "240200", "吉林": "240300", "辽源": "240400", "通化": "240500",
        # 黑龙江省
        "哈尔滨": "220200", "伊春": "220300", "绥化": "220400", "大庆": "220500", "齐齐哈尔": "220600", "牡丹江": "220700", "佳木斯": "220800", "鹤岗": "221000", "黑河": "221200", "大兴安岭": "221400",
        # 江苏省
        "南京": "070200", "苏州": "070300", "无锡": "070400", "常州": "070500", "昆山": "070600", "常熟": "070700", "扬州": "070800", "南通": "070900", "镇江": "071000", "徐州": "071100", "连云港": "071200", "盐城": "071300", "张家港": "071400", "丹阳": "072100",
        # 浙江省
        "杭州": "080200", "宁波": "080300", "温州": "080400", "绍兴": "080500", "金华": "080600", "嘉兴": "080700", "台州": "080800", "湖州": "080900", "丽水": "081000", "舟山": "081100", "衢州": "081200", "海宁": "081600",
        # 安徽省
        "合肥": "150200", "芜湖": "150300", "安庆": "150400", "马鞍山": "150500", "蚌埠": "150600", "阜阳": "150700", "铜陵": "150800", "滁州": "150900", "黄山": "151000", "淮南": "151100", "六安": "151200", "巢湖": "151300", "宣城": "151400", "池州": "151500",
        # 福建省
        "福州": "110200", "厦门": "110300", "泉州": "110400", "漳州": "110500", "莆田": "110600", "三明": "110700", "南平": "110800", "宁德": "110900", "龙岩": "111000",
        # 江西省
        "南昌": "130200", "九江": "130300", "赣州": "130800", "抚州": "131100",
        # 山东省
        "济南": "120200", "青岛": "120300", "烟台": "120400", "潍坊": "120500", "威海": "120600", "淄博": "120700", "临沂": "120800", "济宁": "120900", "东营": "121000", "泰安": "121100", "日照": "121200", "德州": "121300", "菏泽": "121400",
        # 河南省
        "郑州": "170200", "洛阳": "170300", "开封": "170400", "邓州": "172000", "鹤壁": "171700",
        # 湖北省
        "武汉": "180200", "宜昌": "180300", "黄石": "180400", "襄樊": "180500", "十堰": "180600", "荆州": "180700", "荆门": "180800", "孝感": "180900", "鄂州": "181000", "恩施": "181800",
        # 湖南省
        "长沙": "190200", "株洲": "190300", "湘潭": "190400", "衡阳": "190500", "岳阳": "190600", "常德": "190700", "益阳": "190800", "郴州": "190900", "邵阳": "191000", "怀化": "191100", "娄底": "191200", "永州": "191300", "张家界": "191400",
        # 广东省
        "广州": "030200", "惠州": "030300", "汕头": "030400", "珠海": "030500", "佛山": "030600", "中山": "030700", "东莞": "030800", "从化": "031000", "韶关": "031400", "江门": "031500", "增城": "031600", "湛江": "031700", "肇庆": "031800", "清远": "031900", "潮州": "032000", "河源": "032100", "揭阳": "032200", "茂名": "032300", "汕尾": "032400", "顺德": "032500",
        # 广西
        "南宁": "140200", "桂林": "140300", "柳州": "140400", "北海": "140500", "防城港": "140800", "贵港": "141000", "河池": "141200", "贺州": "141500",
        # 海南省
        "海口": "100200", "三亚": "100300", "儋州": "100800", "东方": "100900", "定安": "101100",
        # 四川省
        "成都": "090200", "绵阳": "090300", "乐山": "090400", "泸州": "090500", "德阳": "090600", "宜宾": "090700", "自贡": "090800", "内江": "090900", "攀枝花": "091000", "广安": "091300", "广元": "091600", "达州": "091700", "甘孜": "092100",
        # 贵州省
        "贵阳": "260200", "遵义": "260300",
        # 云南省
        "昆明": "250200", "曲靖": "250300", "玉溪": "250400", "大理": "250500", "丽江": "250600", "蒙自": "250700", "开远": "250800", "个旧": "250900", "红河": "251000", "德宏": "251600", "迪庆": "252000",
        # 西藏
        "拉萨": "300200", "日喀则": "300300",
        # 陕西省
        "西安": "200200", "咸阳": "200300", "宝鸡": "200400", "铜川": "200500", "延安": "200600", "汉中": "200900",
        # 甘肃省
        "兰州": "270200", "金昌": "270300", "定西": "271100", "甘南": "271500",
        # 青海省
        "西宁": "320200", "海东": "320300", "海西": "320400", "海北": "320500", "黄南": "320600", "海南": "320700", "果洛": "320800",
        # 宁夏
        "银川": "290200", "固原": "290600",
        # 新疆
        "乌鲁木齐": "310200", "克拉玛依": "310300", "喀什": "310400", "哈密": "310700", "和田": "311600",
        # 港澳台
        "香港": "330000", "澳门": "340000", "台湾": "350000", "国外": "360000",
    }

    def build_search_url(self, keyword: str, city_code: str) -> str:
        base = "https://q.yingjiesheng.com/jobs/search"
        params = f"?keyword={keyword}"
        if city_code:
            params += f"&jobarea={city_code}"
        return base + params

    async def check_login(self, page) -> bool:
        """应届生求职浏览搜索结果不需要登录。"""
        return True

    async def apply_city_filter(self, page, city: str):
        """应届生求职 UI 城市筛选：快捷城市列表点击 → 非快捷城市通过 URL 参数跳转。"""
        try:
            # --- Step 1: 检查快捷城市列表（全国, 北京, 上海, 广州, 深圳, 天津, 重庆, 南京, 杭州, 成都, 武汉, 西安） ---
            # 页面有两组 .area-option-item，第一组不可见(w=0)，第二组可见
            clicked = await page.evaluate("""
                (cityName) => {
                    const items = document.querySelectorAll('.area-option-item');
                    for (const item of items) {
                        if (item.textContent.trim() === cityName && item.getBoundingClientRect().width > 50) {
                            item.click();
                            return 'quick';
                        }
                    }
                    return false;
                }
            """, city)

            if clicked == "quick":
                logger.warning("[yingjiesheng] clicked quick city: %s", city)
                await page.wait_for_timeout(3000)
                return

            # --- Step 2: 非快捷城市 → 通过 URL 参数直接跳转 ---
            city_code = self.get_city_code(city)
            if not city_code:
                logger.warning("[yingjiesheng] city '%s' has no code, skipping", city)
                return

            # 获取当前 URL 的 keyword 参数
            current_url = page.url
            keyword = ""
            if "keyword=" in current_url:
                keyword = current_url.split("keyword=")[1].split("&")[0]

            new_url = self.build_search_url(keyword, city_code)

            # 如果目标 URL 与当前 URL 相同且有城市代码，跳过导航（避免清空已捕获的数据）
            # city_code 为空（全国）时仍需导航以确保页面状态正确
            if city_code and new_url.rstrip("/") == current_url.rstrip("/"):
                logger.warning("[yingjiesheng] already on city URL, skipping navigation")
                return

            logger.warning("[yingjiesheng] navigating to city URL: %s", new_url)

            # 清空旧的拦截数据，避免返回上一次搜索的结果
            self._captured_data.clear()

            await page.goto(new_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

        except Exception as exc:
            logger.warning("[yingjiesheng] city filter failed: %s", exc)

    async def on_response_text(self, url: str, body_text: str, captured_data: list):
        """拦截 youngapi 的职位搜索 API 响应。"""
        if "/job/" not in url and "/search" not in url and "/list" not in url:
            return
        try:
            if not body_text or len(body_text) < 10:
                return
            body = _json.loads(body_text)
            # 尝试多种 API 响应格式
            items = []
            if isinstance(body, dict):
                # 格式1: {"resultbody": {"searchData": {"joblist": {"items": [...]}}}}
                resultbody = body.get("resultbody") or {}
                if isinstance(resultbody, dict):
                    search_data = resultbody.get("searchData") or {}
                    if isinstance(search_data, dict):
                        joblist = search_data.get("joblist") or {}
                        if isinstance(joblist, dict):
                            items = joblist.get("items") or []
                # 格式2: {"data": {"jobList": [...]}}
                if not items:
                    data = body.get("data") or {}
                    if isinstance(data, dict):
                        items = data.get("jobList") or data.get("list") or data.get("items") or []
                # 格式3: {"resultbody": {"job": {"items": [...]}}}
                if not items:
                    resultbody = body.get("resultbody") or {}
                    if isinstance(resultbody, dict):
                        job = resultbody.get("job") or {}
                        items = job.get("items") or []
                # 格式4: {"list": [...]}
                if not items:
                    items = body.get("list") or []
            if isinstance(items, list) and items:
                captured_data.extend(items)
        except Exception as exc:
            logger.debug("[yingjiesheng] API parse err: %s", exc)

    async def extract_jobs(self, page, limit: int, city: str = "") -> List[Dict]:
        """从 API 拦截数据或 DOM 提取职位。"""
        # 关闭弹窗广告
        await self._close_popups(page)

        if hasattr(self, "_captured_data") and self._captured_data:
            return self._parse_api_jobs(self._captured_data)[:limit]

        # 滚动页面触发懒加载
        await page.evaluate("window.scrollTo(0, 600)")
        await page.wait_for_timeout(2000)

        return await self._extract_jobs_dom(page, limit)

    async def _close_popups(self, page):
        """关闭页面上的弹窗广告。"""
        try:
            await page.evaluate("""
                () => {
                    // 删除弹窗容器 (el-dialog, v-modal 等)
                    const popupSelectors = [
                        '.el-dialog__wrapper',
                        '.v-modal',
                        '.el-overlay',
                        '[class*="dialog__wrapper"]',
                        '[class*="operate-popup"]',
                    ];
                    for (const sel of popupSelectors) {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    }
                    // 删除所有 fixed 定位的大尺寸遮罩/弹窗
                    document.querySelectorAll('*').forEach(el => {
                        const style = getComputedStyle(el);
                        if (style.position === 'fixed') {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 200 && rect.height > 200 && el.id !== 'head') {
                                el.remove();
                            }
                        }
                    });
                    // 恢复 body 滚动
                    document.body.style.overflow = '';
                    document.documentElement.style.overflow = '';
                }
            """)
            await page.wait_for_timeout(500)
        except Exception as exc:
            logger.debug("[yingjiesheng] close popups failed: %s", exc)

    def _parse_api_jobs(self, items: list) -> List[Dict]:
        """解析 API 拦截的职位数据。"""
        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            # 优先从顶层字段提取（应届生 API 格式）
            title = item.get("jobname") or item.get("jobName") or item.get("title") or ""
            company = item.get("coname") or item.get("companyName") or item.get("company") or ""
            salary = item.get("providesalary") or item.get("provideSalaryString") or item.get("salary") or ""
            city = item.get("jobarea") or item.get("jobAreaString") or item.get("city") or ""
            experience = item.get("workyear") or item.get("workYearString") or ""
            education = item.get("degree") or item.get("degreeString") or ""
            job_id = item.get("jobid") or ""
            href = item.get("jumpUrlHttp") or item.get("jobHref") or item.get("url") or ""
            if not href and job_id:
                href = f"https://young.yingjiesheng.com/pc/jobdetail?jobid={job_id}"

            tags_raw = item.get("jobtag") or item.get("jobTags") or item.get("tags") or []
            if isinstance(tags_raw, str):
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            elif isinstance(tags_raw, list):
                tags = [t.get("jobTagName", t) if isinstance(t, dict) else str(t) for t in tags_raw]
            else:
                tags = []

            raw = f"{title}\n{company}\n{city}\n{salary}"
            if experience:
                raw += f"\n经验：{experience}"
            if education:
                raw += f"\n学历：{education}"
            if tags:
                raw += f"\n技能：{' '.join(tags[:5])}"

            results.append({
                "platform": "yingjiesheng",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })
        return results

    async def _extract_jobs_dom(self, page, limit: int) -> List[Dict]:
        """DOM 抓取：从 search-list-href 链接的 URL property 参数解析职位数据。"""
        try:
            await page.wait_for_selector(".search-list-href", timeout=15000)
        except Exception:
            logger.warning("[yingjiesheng] DOM: 职位列表未找到")
            return []

        data = await page.evaluate("""
            (limit) => {
                // 获取当前选中的城市
                let currentCity = '';
                const activeArea = document.querySelector('.area-option-item.active');
                if (activeArea) currentCity = activeArea.textContent.trim();

                const links = document.querySelectorAll('a.search-list-href');
                const results = [];
                for (let i = 0; i < Math.min(links.length, limit); i++) {
                    const a = links[i];
                    const href = a.href || '';
                    let jobData = {};
                    try {
                        const url = new URL(href);
                        const prop = url.searchParams.get('property');
                        if (prop) jobData = JSON.parse(prop);
                    } catch(e) {}
                    const text = a.textContent.trim();
                    // 从链接父元素中获取城市信息
                    const parent = a.closest('.search-list-item-wrapper') || a.parentElement;
                    let city = currentCity;
                    if (parent) {
                        const cityEl = parent.querySelector('.search-list-area, .area, .city');
                        if (cityEl) city = cityEl.textContent.trim() || currentCity;
                    }
                    results.push({
                        href: href,
                        text: text.substring(0, 200),
                        jobTitle: jobData.jobTitle || '',
                        companyName: jobData.companyName || '',
                        salary: jobData.monthSalary || '',
                        city: city,
                    });
                }
                return results;
            }
        """, limit)

        results = []
        for item in data:
            title = item.get("jobTitle", "")
            company = item.get("companyName", "")
            salary = item.get("salary", "")
            href = item.get("href", "")
            city = item.get("city", "")

            if not title:
                text = item.get("text", "")
                parts = text.split()
                if parts:
                    title = parts[0]

            raw = f"{title}\n{company}\n{city}\n{salary}"

            results.append({
                "platform": "yingjiesheng",
                "source_url": href,
                "raw_text": raw.strip(),
                "job_title": title,
                "company_name": company or "未知公司",
                "city": city,
                "salary_range": salary or None,
            })

        logger.info("[yingjiesheng] DOM 提取 %d 条结果", len(results))
        return results
