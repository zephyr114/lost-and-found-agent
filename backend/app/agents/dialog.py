"""对话式发布 Agent：多轮追问 + 槽位填充（规则优先，可选 LLM 增强）。

设计：
- 每轮把用户输入合并进草稿（复用 extract_item_attributes 的规则引擎）
- 检查必填槽位（标题 / 类别 / 地点 / 时间），缺什么问什么
- 全部齐全后返回 done=True，前端即可一键发布
- 不依赖 LLM 也能工作；配置 LLM_API_KEY 后可让回复更自然（后续可扩展）
"""

import re
from datetime import datetime, time, timedelta

from app.agents.matching import CATEGORIES, extract_item_attributes

# 必填槽位（顺序即追问顺序）
REQUIRED_FIELDS = ["title", "category", "location", "event_time"]

CAMPUS_LOCATIONS = [
    "正心楼",
    "创智楼",
    "精诚楼",
    "绍信学生公寓",
    "绍雅居",
    "绍味堂",
    "竞越体育运动中心",
    "青越文化活动中心",
    "芯越科创中心",
    "知行大道",
    "阳明桥",
    "求新桥",
    "守正桥",
    "力行桥",
    "笃学桥",
    "信雅路",
    "致诚路",
    "北门",
    "东门",
    "南门",
    "西门",
    "其他",
]

LOCATION_ALIASES = {
    "学生公寓": "绍信学生公寓",
    "公寓": "绍信学生公寓",
    "宿舍": "绍信学生公寓",
    "寝室": "绍信学生公寓",
    "食堂": "绍味堂",
    "饭堂": "绍味堂",
    "餐厅": "绍味堂",
    "操场": "竞越体育运动中心",
    "体育馆": "竞越体育运动中心",
    "体育中心": "竞越体育运动中心",
    "活动中心": "青越文化活动中心",
    "科创中心": "芯越科创中心",
    "科创": "芯越科创中心",
    "正心": "正心楼",
    "创智": "创智楼",
    "精诚": "精诚楼",
}

CATEGORY_ALIASES = {
    "手机": "电子数码",
    "耳机": "电子数码",
    "电脑": "电子数码",
    "平板": "电子数码",
    "充电宝": "电子数码",
    "校园卡": "证件卡类",
    "学生证": "证件卡类",
    "身份证": "证件卡类",
    "钱包": "钱包箱包",
    "书包": "钱包箱包",
    "背包": "钱包箱包",
    "雨伞": "雨伞水杯",
    "水杯": "雨伞水杯",
    "保温杯": "雨伞水杯",
    "钥匙": "钥匙",
    "书": "书籍文具",
    "课本": "书籍文具",
    "衣服": "衣物饰品",
    "眼镜": "衣物饰品",
}

TIME_WORDS = {
    "刚才": 0,
    "刚刚": 0,
    "今天": 0,
    "今早": 0,
    "今晚": 0,
    "昨天": 1,
    "昨晚": 1,
    "前天": 2,
    "大前天": 3,
    "上周": 7,
    "上星期": 7,
}


def _parse_time(text: str) -> str | None:
    """从自然语言中解析事件时间，返回 ISO 字符串。"""
    days = None
    for word, offset in TIME_WORDS.items():
        if word in text:
            days = offset
            break
    if days is None:
        return None

    hour = 12
    m = re.search(r"(\d{1,2})\s*[点时]", text)
    if m:
        hour = min(max(int(m.group(1)), 0), 23)
    elif "中午" in text:
        hour = 12
    elif "下午" in text:
        hour = 15
    elif "晚上" in text or "晚" in text:
        hour = 19
    elif "早上" in text or "上午" in text:
        hour = 9

    day = datetime.now().date() - timedelta(days=days)
    return datetime.combine(day, time(hour, 0)).strftime("%Y-%m-%dT%H:%M:%S")


def _normalize_location(attrs: dict, text: str) -> str | None:
    """把地点归一化到校园地点（支持“一教/活动中心”等别名）。"""
    candidate = attrs.get("location") or ""
    for alias, full in LOCATION_ALIASES.items():
        if alias in candidate or alias in text:
            return full
    for full in CAMPUS_LOCATIONS:
        if full in candidate or full in text:
            return full
    # 规则引擎抽到了但不在校园列表里：保留原文（用户可改）
    return candidate or None


def _normalize_category(attrs: dict, text: str) -> str | None:
    cat = attrs.get("category") or ""
    if cat in CATEGORIES:
        return cat
    for alias, full in CATEGORY_ALIASES.items():
        if alias in cat or alias in text:
            return full
    return cat or None


def _clean_title(raw: str) -> str:
    """从用户第一句话提取干净的物品标题，例如「我在图书馆丢了个黑色耳机」→「黑色耳机」。"""
    text = raw.split("。")[0].split("\n")[0].strip()
    # 口语前缀
    text = re.sub(r"^(我在|我今天在|我昨天在|我在学校|我|今天|昨天|刚才)", "", text).strip()
    text = re.sub(r"^(在|于)", "", text).strip()
    # 开头地点
    for loc in CAMPUS_LOCATIONS:
        if text.startswith(loc):
            text = text[len(loc):]
            break
    else:
        for alias in LOCATION_ALIASES:
            if text.startswith(alias):
                text = text[len(alias):]
                break
    text = re.sub(r"^(在|于)", "", text).strip()
    # 动词 / 量词
    text = re.sub(r"^(丢了个|丢了|遗失了一个|遗失了|遗失|捡了个|捡到|拾到|拾获|捡了)", "", text)
    text = re.sub(r"^(一个|一只|一把|一件|一张|一条|个|只|把|件|张|条)", "", text).strip()
    # 只取第一个短句
    text = re.split(r"[，,；;]", text)[0].strip()
    return text.strip(" ，,。！!？?")[:30]


def merge_into_draft(draft: dict, text: str) -> dict:
    """把用户输入合并进草稿，返回新草稿（不修改入参）。"""
    merged = {k: (draft.get(k) or "") for k in ["title", "category", "color", "brand", "location", "event_time", "description"]}
    attrs = extract_item_attributes(text)

    for field in ("category", "color", "brand"):
        if attrs.get(field) and not merged[field]:
            merged[field] = attrs[field]

    category = _normalize_category(attrs, text)
    if category and not merged["category"]:
        merged["category"] = category

    location = _normalize_location(attrs, text)
    if location and not merged["location"]:
        merged["location"] = location

    if not merged["event_time"]:
        parsed = _parse_time(text)
        if parsed:
            merged["event_time"] = parsed

    if not merged["title"]:
        cleaned = _clean_title(text)
        if cleaned:
            merged["title"] = cleaned

    if not merged["description"] and len(text) >= 12:
        merged["description"] = text.strip()[:200]

    return merged


def _next_field(draft: dict) -> str | None:
    for field in REQUIRED_FIELDS:
        if not draft.get(field):
            return field
    return None


def _question_for(field: str, item_type: str) -> tuple[str, list[str]]:
    """返回（追问文案, 快捷选项）。"""
    lost = item_type == "lost"
    if field == "title":
        return ("先说说具体是什么东西？比如「黑色双肩包」「校园卡」。", [])
    if field == "category":
        return ("它属于哪一类？可以点下面的选项，也可以直接说。", CATEGORIES)
    if field == "location":
        verb = "丢" if lost else "捡到"
        return (f"是在哪里{verb}的？", CAMPUS_LOCATIONS)
    if field == "event_time":
        verb = "丢失" if lost else "拾获"
        return (f"大概是什么时候{verb}的？", ["今天", "昨天", "前天", "上周"])
    return ("", [])


def _progress(draft: dict) -> int:
    filled = sum(1 for f in REQUIRED_FIELDS if draft.get(f))
    return round(filled / len(REQUIRED_FIELDS) * 100)


def dialog_step(text: str, draft: dict | None, item_type: str = "lost") -> dict:
    """执行一轮对话：合并输入 → 判断缺失 → 生成下一问。"""
    text = (text or "").strip()
    draft = merge_into_draft(draft or {}, text) if text else {k: (draft or {}).get(k, "") for k in
                                                               ["title", "category", "color", "brand", "location", "event_time", "description"]}

    field = _next_field(draft)
    done = field is None

    if done:
        reply = "信息齐全了，我帮你整理好了 👇 确认无误就可以直接发布。"
        options: list[str] = []
    else:
        question, options = _question_for(field, item_type)
        learned = []
        if draft.get("category"):
            learned.append(draft["category"])
        if draft.get("color"):
            learned.append(draft["color"])
        if draft.get("location"):
            learned.append(draft["location"])
        prefix = f"好的，记下了「{'、'.join(learned)}」。" if learned else ""
        reply = prefix + question

    return {
        "reply": reply,
        "draft": draft,
        "missing": [f for f in REQUIRED_FIELDS if not draft.get(f)],
        "next_field": field,
        "options": options,
        "done": done,
        "progress": _progress(draft),
    }
