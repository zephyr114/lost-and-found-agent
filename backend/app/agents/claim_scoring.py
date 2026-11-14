"""认领描述可信度评分：用现有匹配引擎给「认领说明」与「招领物品」算相似度。

用途：帮助拾获者判断认领人是否真的是失主（防冒领），分数只作参考，不自动决策。
"""

from app.models.item import Item


def score_claim(item: Item, description: str) -> dict:
    """返回 {score, verdict, reasons, suggestions}。

    - 把认领描述当作「失物描述」，与招领物品做 7 维匹配
    - verdict: high（≥80，信息高度吻合）/ medium（≥55，部分吻合）/ low（信息不足或矛盾）
    """
    from app.agents.matching import calculate_match_score, counterfactual_suggestions, extract_item_attributes

    attrs = extract_item_attributes(description or "")
    pseudo = Item(
        item_type="lost",
        title=attrs.get("title") or (description or item.title)[:30],
        category=attrs.get("category") or item.category,
        description=description,
        color=attrs.get("color") or None,
        brand=attrs.get("brand") or None,
        location=attrs.get("location") or item.location,
        event_time=item.event_time,
        latitude=item.latitude,
        longitude=item.longitude,
        user_id=0,
        status="active",
        audit_status="approved",
    )
    result = calculate_match_score(pseudo, item)
    score = int(result.get("score", 0))
    verdict = "high" if score >= 80 else "medium" if score >= 55 else "low"
    suggestions = counterfactual_suggestions(pseudo, item, limit=2)
    return {
        "score": score,
        "verdict": verdict,
        "reasons": result.get("reasons", []),
        "suggestions": suggestions,
    }
