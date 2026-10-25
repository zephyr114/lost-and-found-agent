"""演示数据脚本：创建演示用户、物品、认领申请并运行智能匹配。

用法（backend 目录下）：
    .venv\\Scripts\\python scripts\\seed_demo.py

幂等：已存在的演示数据会跳过。
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents import matching
from app.core.security import hash_password
from app.database.session import Base, SessionLocal, engine
from app.models.announcement import Announcement
from app.models.claim import Claim
from app.models.item import Item
from app.models.user import User

DEMO_USERS = [
    {"username": "demo_user1", "email": "user1@example.com", "phone": "13800000001", "password": "demo123456"},
    {"username": "demo_user2", "email": "user2@example.com", "phone": "13800000002", "password": "demo123456"},
    {"username": "demo_user3", "email": "user3@example.com", "phone": "13800000003", "password": "demo123456"},
]

DEMO_ITEMS = [
    # 一对高匹配：黑色苹果耳机（失物 / 招领）
    {
        "user": "demo_user1", "item_type": "lost", "title": "丢失黑色苹果耳机",
        "category": "电子数码", "color": "黑色", "brand": "苹果",
        "location": "图书馆三楼", "latitude": 31.2304, "longitude": 121.4737,
        "event_days_ago": 2, "description": "耳机盒底部有刻字 LZ，左耳有轻微划痕",
    },
    {
        "user": "demo_user2", "item_type": "found", "title": "捡到黑色苹果耳机",
        "category": "电子数码", "color": "黑色", "brand": "苹果",
        "location": "图书馆三楼自习区", "latitude": 31.2305, "longitude": 121.4738,
        "event_days_ago": 1, "description": "耳机盒底部有刻字，外观完好",
    },
    # 一对中匹配：黑色钱包
    {
        "user": "demo_user3", "item_type": "lost", "title": "丢失黑色钱包",
        "category": "钱包箱包", "color": "黑色", "brand": None,
        "location": "食堂二楼", "latitude": 31.2310, "longitude": 121.4740,
        "event_days_ago": 5, "description": "内有校园卡和少量现金",
    },
    {
        "user": "demo_user1", "item_type": "found", "title": "捡到黑色钱包",
        "category": "钱包箱包", "color": "黑色", "brand": None,
        "location": "食堂门口", "latitude": 31.2311, "longitude": 121.4741,
        "event_days_ago": 4, "description": "内有卡片若干，无现金",
    },
    # 其他物品
    {
        "user": "demo_user2", "item_type": "lost", "title": "丢失校园卡",
        "category": "证件卡类", "color": None, "brand": None,
        "location": "操场", "latitude": None, "longitude": None,
        "event_days_ago": 10, "description": "卡号后四位 3456，贴有蓝色卡贴",
    },
    {
        "user": "demo_user3", "item_type": "found", "title": "捡到一把雨伞",
        "category": "雨伞水杯", "color": "藏青色", "brand": None,
        "location": "教学楼 A 座", "latitude": None, "longitude": None,
        "event_days_ago": 3, "description": "伞柄处有姓名缩写贴纸",
    },
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. 演示用户
        users: dict[str, User] = {}
        for u in DEMO_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                users[u["username"]] = existing
                print(f"跳过已存在用户: {u['username']}")
                continue
            user = User(
                username=u["username"], email=u["email"], phone=u["phone"],
                password_hash=hash_password(u["password"]),
                role="user", status="active", credit_score=100,
            )
            db.add(user)
            users[u["username"]] = user
            print(f"创建用户: {u['username']} / 密码 {u['password']}")
        db.flush()  # 立即写入，使新用户获得 id

        # 2. 物品（审核通过）
        item_by_key: dict[str, Item] = {}
        for spec in DEMO_ITEMS:
            key = f"{spec['user']}_{spec['item_type']}_{spec['title']}"
            exists = (
                db.query(Item)
                .filter(Item.user_id == users[spec["user"]].id, Item.title == spec["title"])
                .first()
            )
            if exists:
                item_by_key[key] = exists
                print(f"跳过已存在物品: {spec['title']}")
                continue
            item = Item(
                user_id=users[spec["user"]].id,
                item_type=spec["item_type"],
                title=spec["title"],
                category=spec["category"],
                color=spec["color"],
                brand=spec["brand"],
                location=spec["location"],
                latitude=spec["latitude"],
                longitude=spec["longitude"],
                event_time=datetime.now(timezone.utc) - timedelta(days=spec["event_days_ago"]),
                description=spec["description"],
                images=[],
                status="active",
                audit_status="approved",
            )
            db.add(item)
            item_by_key[key] = item
            print(f"创建物品: [{spec['item_type']}] {spec['title']}")
        db.commit()

        # 3. 认领申请：demo_user3 认领 demo_user1 发布的钱包
        wallet = item_by_key.get("demo_user1_found_捡到黑色钱包")
        if wallet and not db.query(Claim).filter(Claim.item_id == wallet.id).first():
            db.add(
                Claim(
                    item_id=wallet.id,
                    applicant_id=users["demo_user3"].id,
                    proof_description="钱包内有我的校园卡，卡面贴有蓝色卡贴",
                    proof_images=[],
                    contact="13800000003",
                    status="pending",
                )
            )
            db.commit()
            print("创建认领申请: demo_user3 → 捡到黑色钱包")

        # 4. 系统公告
        if not db.query(Announcement).first():
            db.add(
                Announcement(
                    title="欢迎使用失物招领智能平台",
                    content="请在发布信息时如实描述物品特征；认领时请提供只有物主才知道的证明，谨防诈骗。",
                    status="active",
                )
            )
            db.commit()
            print("创建系统公告")

        # 5. 对演示物品运行智能匹配
        for key, item in item_by_key.items():
            if item.item_type == "lost":
                matching.run_matching_pipeline(db, item.id, user_id=item.user_id, notify=False)
                print(f"已对「{item.title}」运行智能匹配")

        print("\n演示数据完成！")
        print("登录账号：demo_user1 / demo_user2 / demo_user3，密码均为 demo123456")
        print("管理员：admin / admin123456（.env 的 ADMIN_* 配置）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
