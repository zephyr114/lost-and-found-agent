# -*- coding: utf-8 -*-
"""通过 Cloudflare API 创建命名隧道 + DNS 记录，供 cloudflared 使用。

用法：
    set CF_API_TOKEN=xxxx
    python scripts/cf_setup.py

需要的 Token 权限：
    Account → Cloudflare Tunnel → Edit
    Zone    → DNS              → Edit
    Zone    → Zone             → Read
"""
import json
import os
import sys

import httpx

API = "https://api.cloudflare.com/client/v4"
HOSTNAME = "hdulosttrack.eu.cc"
TUNNEL_NAME = "hdu-lost-found"
LOCAL_SERVICE = "http://localhost:8001"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_tunnel_info.json")

token = os.environ.get("CF_API_TOKEN", "").strip()
if not token:
    print("缺少环境变量 CF_API_TOKEN")
    sys.exit(1)

c = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {token}"}, timeout=30)


def call(method, path, **kw):
    r = c.request(method, path, **kw)
    data = r.json()
    if not data.get("success"):
        raise SystemExit(f"API 失败 {path}: {json.dumps(data.get('errors'), ensure_ascii=False)}")
    return data["result"]


accounts = call("GET", "/accounts")
if not accounts:
    raise SystemExit("未找到账户，Token 权限可能不足")
account_id = accounts[0]["id"]
print("account:", account_id, accounts[0].get("name"))

zones = call("GET", "/zones", params={"name": HOSTNAME})
if not zones:
    raise SystemExit(f"未找到 zone {HOSTNAME}，请确认域名已添加到 Cloudflare")
zone_id = zones[0]["id"]
print("zone:", zone_id, zones[0]["name"])

# 1. 隧道（已存在则复用）
found = call("GET", f"/accounts/{account_id}/cfd_tunnel", params={"name": TUNNEL_NAME, "is_deleted": "false"})
if found:
    tunnel = found[0]
    print("复用隧道:", tunnel["id"])
else:
    tunnel = call("POST", f"/accounts/{account_id}/cfd_tunnel",
                  json={"name": TUNNEL_NAME, "config_src": "cloudflare"})
    print("创建隧道:", tunnel["id"])
tunnel_id = tunnel["id"]

# 2. 隧道配置：hdulosttrack.eu.cc -> 本地 8001
call("PUT", f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations", json={
    "config": {
        "ingress": [
            {"hostname": HOSTNAME, "service": LOCAL_SERVICE},
            {"service": "http_status:404"},
        ]
    }
})
print("隧道配置已写入")

# 3. DNS：CNAME -> <tunnel_id>.cfargotunnel.com（橙色云）
records = call("GET", f"/zones/{zone_id}/dns_records", params={"name": HOSTNAME})
existing = {r["type"]: r for r in records}
if "CNAME" in existing:
    call("PUT", f"/zones/{zone_id}/dns_records/{existing['CNAME']['id']}", json={
        "type": "CNAME", "name": HOSTNAME,
        "content": f"{tunnel_id}.cfargotunnel.com", "proxied": True,
    })
    print("DNS CNAME 已更新")
else:
    for r in records:
        call("DELETE", f"/zones/{zone_id}/dns_records/{r['id']}")
    call("POST", f"/zones/{zone_id}/dns_records", json={
        "type": "CNAME", "name": HOSTNAME,
        "content": f"{tunnel_id}.cfargotunnel.com", "proxied": True,
    })
    print("DNS CNAME 已创建")

# 4. 取隧道运行 token
run_token = call("GET", f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token")

info = {
    "account_id": account_id,
    "zone_id": zone_id,
    "tunnel_id": tunnel_id,
    "hostname": HOSTNAME,
    "service": LOCAL_SERVICE,
    "token": run_token,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)
print("已保存:", OUT)
print("tunnel_id:", tunnel_id)
