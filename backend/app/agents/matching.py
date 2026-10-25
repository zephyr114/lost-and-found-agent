"""Lost-and-Found Matching Agent

智能匹配 Agent：解析物品属性 → 搜索相似物品 → 计算匹配分数 → 解释原因 → 通知用户 → 记录日志。

工具函数（与执行说明书一致）：
    extract_item_attributes()   提取物品名称 / 类别 / 颜色 / 品牌 / 地点
    search_similar_items()      搜索数据库中的相似物品
    calculate_match_score()     计算匹配分数
    query_location_distance()   计算地点距离
    create_match_notification() 创建匹配通知
    submit_audit_task()         发现高风险内容时标记转人工审核
    send_user_message()         发送用户消息

默认使用确定性规则引擎（无需外部服务）；配置 LLM_API_KEY 后，
属性提取可升级为调用 DeepSeek 等 OpenAI 兼容接口。
"""

import difflib
import json
import re
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent_log import AgentLog
from app.models.item import Item
from app.models.match import Match
from app.services import message_service
from app.utils.geo import haversine_km

# ---------------- 知识库：颜色 / 品牌 / 类别 ----------------

COLOR_WORDS = [
    "黑色", "白色", "红色", "蓝色", "黄色", "绿色", "灰色", "紫色", "粉色",
    "橙色", "棕色", "银色", "金色", "咖啡色", "深色", "浅色", "米色", "藏青色",
]

BRAND_WORDS = [
    "苹果", "华为", "小米", "三星", "oppo", "vivo", "荣耀", "联想", "戴尔",
    "惠普", "华硕", "索尼", "佳能", "耐克", "阿迪达斯", "新秀丽", "李宁", "安踏",
    "匡威", "优衣库", "无印良品",
]

CATEGORIES = [
    "证件卡类", "电子数码", "钱包箱包", "衣物饰品", "书籍文具",
    "钥匙", "雨伞水杯", "运动器材", "宠物", "其他",
]

# 类别关键词映射（规则引擎用）
CATEGORY_KEYWORDS = {
    "证件卡类": ["证件", "身份证", "校园卡", "学生证", "银行卡", "公交卡", "驾照", "卡包"],
    "电子数码": ["手机", "耳机", "平板", "电脑", "笔记本", "充电宝", "相机", "手表", "数据线"],
    "钱包箱包": ["钱包", "背包", "书包", "手提包", "行李箱", "双肩包", "挎包"],
    "衣物饰品": ["衣服", "外套", "围巾", "帽子", "眼镜", "首饰", "项链", "手链", "手套"],
    "书籍文具": ["书", "课本", "教材", "文具", "笔袋"],
    "钥匙": ["钥匙"],
    "雨伞水杯": ["雨伞", "水杯", "保温杯"],
    "运动器材": ["球拍", "篮球", "足球", "羽毛球", "滑板", "球鞋"],
    "宠物": ["猫", "狗", "宠物"],
}

# 同义 / 近义类别组（部分匹配加分用）
CATEGORY_GROUPS = [
    {"钱包箱包", "衣物饰品"},
    {"电子数码", "运动器材"},
]

# 高风险内容关键词（命中则建议人工审核）
RISK_KEYWORDS = ["现金", "转账", "汇款", "红包", "加微信", "扫码", "银行卡", "密码", "代购", "刷单"]

TYPE_WORDS = ["丢失", "遗失", "丢了", "捡到", "拾获", "寻找", "寻物", "招领", "失物"]

MATCH_THRESHOLD = 40.0  # 低于该分数不生成匹配记录


# ---------------- 工具 1：extract_item_attributes ----------------

def _llm_extract(text: str) -> dict | None:
    """配置了 LLM_API_KEY 时调用大模型提取属性；失败或未配置返回 None。"""
    if not settings.llm_api_key:
        return None
    prompt = (
        "你是失物招领信息解析助手。请从下面的文字中提取物品属性，"
        '只输出 JSON，格式：{"title": "...", "category": "...", "color": "...", "brand": "...", "location": "..."}。'
        f"可选类别：{'、'.join(CATEGORIES)}。\n\n文字：{text}"
    )
    try:
        resp = httpx.post(
            f"{settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 300,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return {k: str(v) if v is not None else None for k, v in data.items()}
    except Exception:
        return None


def extract_item_attributes(text: str) -> dict:
    """从文本中提取物品属性（规则引擎 + 可选 LLM 增强）。"""
    llm_result = _llm_extract(text)
    if llm_result and any(llm_result.values()):
        return llm_result

    attrs = {"title": "", "category": "", "color": "", "brand": "", "location": ""}

    # 颜色
    for word in COLOR_WORDS:
        if word in text:
            attrs["color"] = word
            break
    # 品牌
    lowered = text.lower()
    for word in BRAND_WORDS:
        if word.lower() in lowered:
            attrs["brand"] = word
            break
    # 类别
    for cat in CATEGORIES:
        if cat in text:
            attrs["category"] = cat
            break
    if not attrs["category"]:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                attrs["category"] = cat
                break
    # 地点：匹配 “在/于 …（附近|一带|门口|丢|捡）” 或 “地点：xxx”
    loc_match = re.search(r"(?:在|于)([\u4e00-\u9fa5A-Za-z0-9]{2,20})(?:附近|一带|门口|丢了|丢的|捡到|拾到|丢失)", text)
    if loc_match:
        attrs["location"] = loc_match.group(1)
    else:
        loc2 = re.search(r"地点[:：]\s*([\u4e00-\u9fa5A-Za-z0-9]{2,20})", text)
        if loc2:
            attrs["location"] = loc2.group(1)

    # 标题：清理类型词后的首段
    title = text.split("。")[0].split("\n")[0][:30]
    for w in TYPE_WORDS:
        title = title.replace(w, "")
    attrs["title"] = title.strip(" ，,。！!？?")[:30]
    return attrs


# ---------------- 工具 2：query_location_distance ----------------

def query_location_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float | None:
    """计算两点球面距离（公里）。"""
    return haversine_km(lat1, lon1, lat2, lon2)


# ---------------- 工具 3：calculate_match_score ----------------

def _normalize_title(title: str) -> str:
    text = title or ""
    for w in TYPE_WORDS:
        text = text.replace(w, "")
    return re.sub(r"[\s，,。！!？?、·\-_（）()【】\[\]]+", "", text)


def _title_similarity(a: str, b: str) -> float:
    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def _char_bigram_overlap(a: str, b: str) -> float:
    """中文文本 2-gram 重合率（近似外观特征重合度）。"""
    def grams(text: str) -> set:
        cleaned = re.sub(r"[\s，,。！!？?、·\-_（）()【】\[\]]+", "", text or "")
        return {cleaned[i : i + 2] for i in range(max(len(cleaned) - 1, 0))}

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / min(len(ga), len(gb))


def _to_naive_utc(dt: datetime | None) -> datetime | None:
    """统一转为 UTC 无时区时间，避免 aware / naive 混用报错。"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def calculate_match_score(lost: Item, found: Item) -> dict:
    """计算失物与招领的匹配分数（0-100）并生成中文解释。"""
    score = 0.0
    reasons: list[str] = []
    details: dict = {}

    # 1. 物品类别
    if lost.category and lost.category == found.category:
        score += 30
        reasons.append("物品类别一致")
        details["category"] = lost.category
    else:
        for group in CATEGORY_GROUPS:
            if lost.category in group and found.category in group:
                score += 10
                reasons.append("物品类别相近")
                break

    # 2. 物品名称
    sim = _title_similarity(lost.title, found.title)
    details["title_similarity"] = round(sim, 3)
    if sim >= 0.7:
        score += 15
        reasons.append("物品名称高度相似")
    elif sim >= 0.4:
        score += 10
        reasons.append("物品名称部分相似")
    elif sim >= 0.25:
        score += 5

    # 3. 颜色
    if lost.color and found.color and lost.color == found.color:
        score += 10
        reasons.append("颜色描述一致")
        details["color"] = lost.color

    # 4. 品牌
    if lost.brand and found.brand and lost.brand == found.brand:
        score += 10
        reasons.append("品牌一致")
        details["brand"] = lost.brand

    # 5. 时间差
    lost_time = _to_naive_utc(lost.event_time)
    found_time = _to_naive_utc(found.event_time)
    if lost_time and found_time:
        days = abs((lost_time - found_time).total_seconds()) / 86400.0
        details["time_diff_days"] = round(days, 1)
        if days <= 3:
            score += 15
            reasons.append("丢失和拾获时间相近")
        elif days <= 7:
            score += 10
            reasons.append("时间差在一周内")
        elif days <= 30:
            score += 5
            reasons.append("时间差在一个月内")

    # 6. 地点距离
    km = query_location_distance(lost.latitude or 0, lost.longitude or 0, found.latitude or 0, found.longitude or 0) \
        if all(x is not None for x in (lost.latitude, lost.longitude, found.latitude, found.longitude)) else None
    if km is not None:
        details["distance_km"] = round(km, 2)
        if km <= 1:
            score += 15
            reasons.append("地点距离很近")
        elif km <= 10:
            score += 10
            reasons.append("地点距离较近")
        elif km <= 50:
            score += 5
            reasons.append("地点在同一城市范围")

    # 7. 外观特征（描述文本重合）
    overlap = _char_bigram_overlap(lost.description, found.description)
    details["description_overlap"] = round(overlap, 3)
    if overlap >= 0.3:
        score += 15
        reasons.append("外观特征高度重合")
    elif overlap >= 0.15:
        score += 10
        reasons.append("外观特征部分重合")
    elif overlap > 0:
        score += 5

    return {"score": round(min(score, 100.0), 2), "reasons": reasons, "details": details}


# ---------------- 工具 4：search_similar_items ----------------

def search_similar_items(db: Session, item: Item, limit: int = 10) -> list[tuple[Item, dict]]:
    """搜索与物品类型相反、已审核且可用的候选物品并打分排序。"""
    opposite = "found" if item.item_type == "lost" else "lost"
    candidates = (
        db.query(Item)
        .filter(
            Item.item_type == opposite,
            Item.audit_status == "approved",
            Item.status == "active",
        )
        .all()
    )
    scored = [(cand, calculate_match_score(item, cand)) for cand in candidates]
    scored.sort(key=lambda pair: -pair[1]["score"])
    return scored[:limit]


# ---------------- 工具 5/6：通知与消息 ----------------

def send_user_message(
    db: Session,
    receiver_id: int,
    content: str,
    message_type: str = "system",
    sender_id: int | None = None,
):
    """发送用户消息（封装 message_service）。"""
    return message_service.create_message(db, receiver_id, content, message_type=message_type, sender_id=sender_id)


def create_match_notification(db: Session, item: Item, top_matches: list[Match]) -> None:
    """给物品发布者发送智能匹配提醒。"""
    if not top_matches:
        return
    best = top_matches[0]
    type_text = "失物" if item.item_type == "lost" else "招领"
    content = (
        f"智能匹配提醒：您发布的{type_text}「{item.title}」与 {len(top_matches)} 条信息匹配度较高，"
        f"最高匹配度 {best.match_score} 分（{best.match_reason[0] if best.match_reason else '综合相似'}）。"
        f"可在物品详情页查看匹配推荐。"
    )
    send_user_message(db, item.user_id, content, message_type="match")


# ---------------- 工具 7：submit_audit_task ----------------

def submit_audit_task(text: str) -> dict:
    """发现高风险内容时标记转人工审核。"""
    hit = [kw for kw in RISK_KEYWORDS if kw in (text or "")]
    return {"risk_flagged": bool(hit), "keywords": hit, "action": "manual_review" if hit else "none"}


# ---------------- 日志 ----------------

def _log_tool(
    db: Session,
    user_id: int | None,
    task_type: str,
    tool_name: str,
    input_data: dict | list | None,
    result: dict | list | None,
    status: str = "success",
    elapsed_ms: int = 0,
) -> None:
    db.add(
        AgentLog(
            user_id=user_id,
            task_type=task_type,
            tool_name=tool_name,
            input_data=input_data,
            tool_result=result,
            execution_time_ms=elapsed_ms,
            status=status,
        )
    )
    db.commit()


# ---------------- 流水线 ----------------

def run_matching_pipeline(db: Session, item_id: int, user_id: int | None = None, notify: bool = True) -> list[dict]:
    """对指定物品执行完整匹配流程：提取属性 → 搜索 → 打分 → 落库 → 通知 → 日志。"""
    started = time.perf_counter()
    item = db.get(Item, item_id)
    if item is None:
        return []

    text = f"{item.title} {item.description or ''} 地点：{item.location}"

    # 1. 提取属性
    t0 = time.perf_counter()
    attrs = extract_item_attributes(text)
    _log_tool(
        db, user_id, "item_matching", "extract_item_attributes",
        {"text": text[:200]}, attrs, elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )

    # 1.5 图片识别：物品未填写颜色且有图片时，从首图提取主色补充属性
    if item.images and not item.color:
        t0 = time.perf_counter()
        from app.utils.vision import analyze_image_file, resolve_upload_path

        image_result: dict = {}
        img_path = resolve_upload_path(item.images[0])
        if img_path and img_path.exists():
            image_result = analyze_image_file(img_path)
            if image_result.get("color"):
                item.color = image_result["color"]
                db.commit()
        _log_tool(
            db, user_id, "image_recognition", "analyze_image",
            {"item_id": item.id, "image": item.images[0]}, image_result,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )

    # 2. 搜索相似物品
    t0 = time.perf_counter()
    scored = search_similar_items(db, item)
    _log_tool(
        db, user_id, "item_matching", "search_similar_items",
        {"item_id": item.id, "item_type": item.item_type},
        {"candidate_count": len(scored)},
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )

    # 3. 计算匹配分数并落库（阈值过滤，最多 5 条）
    stored: list[Match] = []
    for cand, result in scored:
        if result["score"] < MATCH_THRESHOLD or len(stored) >= 5:
            continue
        if item.item_type == "lost":
            match = Match(
                lost_item_id=item.id,
                found_item_id=cand.id,
                match_score=result["score"],
                match_reason=result["reasons"],
                status="new",
            )
        else:
            match = Match(
                lost_item_id=cand.id,
                found_item_id=item.id,
                match_score=result["score"],
                match_reason=result["reasons"],
                status="new",
            )
        db.add(match)
        stored.append(match)
    db.commit()

    t0 = time.perf_counter()
    _log_tool(
        db, user_id, "item_matching", "calculate_match_score",
        {"item_id": item.id},
        {"top_scores": [{"score": m.match_score, "reasons": m.match_reason} for m in stored]},
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )

    # 4. 通知用户
    if notify and stored:
        t0 = time.perf_counter()
        create_match_notification(db, item, stored)
        _log_tool(
            db, user_id, "item_matching", "create_match_notification",
            {"item_id": item.id, "receiver_id": item.user_id},
            {"notified_matches": len(stored)},
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )

    # 5. 风险审查
    t0 = time.perf_counter()
    risk = submit_audit_task(text)
    _log_tool(
        db, user_id, "item_matching", "submit_audit_task",
        {"item_id": item.id}, risk, elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )

    total_ms = int((time.perf_counter() - started) * 1000)
    return serialize_matches(db, stored, total_ms)


def serialize_matches(db: Session, matches: list[Match], elapsed_ms: int = 0) -> list[dict]:
    items: dict[int, str] = {}
    ids = {m.lost_item_id for m in matches} | {m.found_item_id for m in matches}
    if ids:
        items = dict(db.query(Item.id, Item.title).filter(Item.id.in_(ids)).all())
    return [
        {
            "id": m.id,
            "lost_item_id": m.lost_item_id,
            "found_item_id": m.found_item_id,
            "match_score": m.match_score,
            "match_reason": m.match_reason or [],
            "status": m.status,
            "created_at": m.created_at,
            "lost_title": items.get(m.lost_item_id),
            "found_title": items.get(m.found_item_id),
            "agent_elapsed_ms": elapsed_ms if i == 0 else 0,
        }
        for i, m in enumerate(matches)
    ]


def background_matching(item_id: int, user_id: int) -> None:
    """后台任务入口：使用独立会话执行匹配流水线。"""
    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        run_matching_pipeline(db, item_id, user_id=user_id, notify=True)
    except Exception:
        db.rollback()
    finally:
        db.close()
