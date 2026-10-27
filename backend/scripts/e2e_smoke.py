"""端到端冒烟测试（API 级）：覆盖注册 → 登录 → 发布 → 审核 → 匹配 → 确认 → 交接 → 故事墙 → 消息。

用法（后端已启动时）：
    python scripts/e2e_smoke.py [base_url]

默认 base_url = http://127.0.0.1:8000
"""

import sys
import uuid

import httpx

# Windows 控制台默认 GBK，强制 UTF-8 以输出中文/emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def uniq(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def check(cond: bool, msg: str) -> None:
    print(("✅ " if cond else "❌ ") + msg)
    if not cond:
        raise SystemExit(1)


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=20)

    # 1. 注册两个用户
    lost_owner = client.post(
        "/api/auth/register",
        json={"username": uniq("e2e_lost"), "email": f"{uniq('e2e1')}@example.com", "password": "secret123"},
    )
    check(lost_owner.status_code == 201, "注册失主")
    lost_token = lost_owner.json()["access_token"]
    lost_refresh = lost_owner.json()["refresh_token"]

    found_owner = client.post(
        "/api/auth/register",
        json={"username": uniq("e2e_found"), "email": f"{uniq('e2e2')}@example.com", "password": "secret123"},
    )
    check(found_owner.status_code == 201, "注册拾获者")
    found_token = found_owner.json()["access_token"]

    # 2. 刷新令牌
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": lost_refresh})
    check(refreshed.status_code == 200, "刷新访问令牌")

    # 3. 发布失物与招领
    lost = client.post(
        "/api/items",
        json={
            "item_type": "lost",
            "title": "E2E 丢失黑色苹果耳机",
            "category": "电子数码",
            "color": "黑色",
            "brand": "苹果",
            "location": "图书馆",
            "latitude": 31.2304,
            "longitude": 121.4737,
            "description": "耳机盒有刻字",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers={"Authorization": f"Bearer {lost_token}"},
    )
    check(lost.status_code == 201, "发布失物")
    lost_id = lost.json()["id"]

    found = client.post(
        "/api/items",
        json={
            "item_type": "found",
            "title": "E2E 捡到黑色苹果耳机",
            "category": "电子数码",
            "color": "黑色",
            "brand": "苹果",
            "location": "图书馆",
            "latitude": 31.2304,
            "longitude": 121.4737,
            "description": "耳机盒有刻字",
            "event_time": "2026-10-20T10:00:00Z",
        },
        headers={"Authorization": f"Bearer {found_token}"},
    )
    check(found.status_code == 201, "发布招领")

    # 4. 管理员登录并审核
    admin = client.post("/api/auth/login", json={"account": "admin@example.com", "password": "admin123456"})
    check(admin.status_code == 200, "管理员登录")
    admin_token = admin.json()["access_token"]

    for item_id in (lost_id, found.json()["id"]):
        r = client.put(
            f"/api/admin/items/{item_id}/audit",
            json={"decision": "approve", "comment": "e2e"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        check(r.status_code == 200, f"审核物品 {item_id}")

    # 5. 智能匹配
    analyzed = client.post(
        "/api/matches/analyze",
        json={"item_id": lost_id},
        headers={"Authorization": f"Bearer {lost_token}"},
    )
    check(analyzed.status_code == 200, "运行智能匹配")
    matches = analyzed.json()["items"]
    check(len(matches) > 0, "产生匹配结果")
    match = next((m for m in matches if m["found_item_id"] == found.json()["id"]), None)
    check(match is not None, "匹配结果包含本次发布的招领")
    check(match["dimensions"] is not None, "匹配结果包含 7 维数据")

    # 6. 确认匹配 + 交接码
    confirmed = client.post(
        f"/api/matches/{match['id']}/confirm",
        headers={"Authorization": f"Bearer {lost_token}"},
    )
    check(confirmed.status_code == 200, "确认匹配")
    code = confirmed.json()["handover_code"]
    check(bool(code), f"获得交接码 {code}")

    # 7. 完成交接
    handover = client.post(
        f"/api/matches/{match['id']}/handover",
        json={"code": code},
        headers={"Authorization": f"Bearer {found_token}"},
    )
    check(handover.status_code == 200, "确认交接")
    check(handover.json()["status"] == "handed_over", "匹配状态为 handed_over")

    # 8. 故事墙
    stories = client.get("/api/matches/stories")
    check(stories.status_code == 200 and any(s["id"] == lost_id for s in stories.json()["items"]), "故事墙包含已找回物品")

    # 9. 消息通知
    inbox = client.get("/api/messages", headers={"Authorization": f"Bearer {lost_token}"})
    check(inbox.status_code == 200 and inbox.json()["total"] > 0, "失主收到通知消息")

    # 10. 统计
    stats = client.get("/api/stats/overview")
    check(stats.status_code == 200 and stats.json()["items_resolved"] >= 1, "统计数据包含已找回数量")

    print("\n🎉 E2E 冒烟测试全部通过")


if __name__ == "__main__":
    main()
