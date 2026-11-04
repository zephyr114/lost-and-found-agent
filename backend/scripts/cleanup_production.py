# -*- coding: utf-8 -*-
"""清理线上 E2E 测试数据，并灌入真实感演示数据。"""
import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://hdulosttrack.eu.cc"
c = httpx.Client(base_url=BASE, timeout=40)


def login(account, password):
    r = c.post("/api/auth/login", json={"account": account, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


def auth(t):
    return {"Authorization": f"Bearer {t}"}


def register(name, pwd="demo123456"):
    r = c.post("/api/auth/register", json={"username": name, "email": f"{name}@example.com", "password": pwd})
    if r.status_code == 201:
        return r.json()["access_token"]
    if r.status_code == 409:
        return login(name, pwd)
    raise SystemExit(f"register {name} failed: {r.status_code} {r.text[:200]}")


admin = login("admin@example.com", "admin123456")
print("admin ok")

# 1. 删除 E2E / 调试 数据
items = c.get("/api/items", params={"size": 100}).json()["items"]
targets = [i for i in items if ("E2E" in i["title"]) or ("调试" in i["title"])]
print("待删除:", [i["title"] for i in targets])
for it in targets:
    r = c.delete(f"/api/admin/items/{it['id']}", headers=auth(admin))
    print("delete", it["id"], r.status_code)

# 2. 演示账号
users = {}
for name in ("demo_user1", "demo_user2", "demo_user3"):
    users[name] = register(name)
    print("user", name, "ok")

# 3. 真实感数据
data = [
    ("demo_user1", "lost", "黑色双肩包（内含笔记本电脑）", "包类", "黑色", "新秀丽", "图书馆",
     "今天下午在图书馆三楼自习区遗失，包内有笔记本电脑和充电器，麻烦捡到的同学联系我，非常感谢！"),
    ("demo_user1", "lost", "苹果 AirPods 耳机", "电子数码", "白色", "苹果", "体育馆",
     "在体育馆羽毛球场地遗失，耳机盒上有一个小挂件，有拾到的同学请联系我。"),
    ("demo_user2", "lost", "校园卡（张同学）", "证件卡类", "蓝色", None, "第一教学楼",
     "课间在第一教学楼遗失，卡号为 22xxxxxx，捡到的同学麻烦联系。"),
    ("demo_user3", "found", "捡到一把黑色雨伞", "生活用品", "黑色", None, "食堂",
     "在食堂二楼捡到一把黑色长柄雨伞，伞柄有磨损，已交至食堂服务台，失主可前来认领。"),
    ("demo_user3", "found", "捡到学生证一张", "证件卡类", "绿色", None, "学生活动中心",
     "在学生活动中心门口捡到学生证一张，姓名为李同学，已交至活动中心值班室。"),
    ("demo_user3", "found", "捡到银色保温杯", "生活用品", "银色", "膳魔师", "第二教学楼",
     "在第二教学楼 2-201 教室捡到银色保温杯一个，杯身有贴纸，请联系认领。"),
]

created = []
for user, typ, title, cat, color, brand, loc, desc in data:
    payload = {
        "item_type": typ, "title": title, "category": cat, "location": loc,
        "event_time": "2026-11-04T09:30:00Z", "description": desc,
    }
    if color:
        payload["color"] = color
    if brand:
        payload["brand"] = brand
    r = c.post("/api/items", json=payload, headers=auth(users[user]))
    if r.status_code != 201:
        print("create failed", title, r.status_code, r.text[:150])
        continue
    iid = r.json()["id"]
    a = c.put(f"/api/admin/items/{iid}/audit", json={"decision": "approve", "comment": "demo"},
              headers=auth(admin))
    print("created", iid, title, "| audit", a.status_code)
    created.append(iid)

stats = c.get("/api/stats/overview").json()
print("stats:", stats)

latest = c.get("/api/items", params={"size": 6, "sort": "newest"}).json()["items"]
print("latest:", [i["title"] for i in latest])
