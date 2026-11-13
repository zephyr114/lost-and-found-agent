"""图像识别工具：本地主色 / 亮度检测（Pillow）+ 可选大模型视觉接口。

说明：
- 默认使用内置规则（零外部依赖）：提取图片主色、亮度等特征。
- 配置 LLM_API_KEY 后，优先调用视觉大模型识别类别 / 颜色 / 品牌 / 描述，失败时回退本地检测。
"""

import base64
import io
import json
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.config import settings as _settings

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / _settings.upload_dir

# 常见颜色名称 → RGB（用于主色归类）
NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "黑色": (0, 0, 0),
    "白色": (255, 255, 255),
    "红色": (255, 0, 0),
    "蓝色": (0, 0, 255),
    "绿色": (0, 128, 0),
    "黄色": (255, 255, 0),
    "灰色": (128, 128, 128),
    "紫色": (128, 0, 128),
    "粉色": (255, 192, 203),
    "橙色": (255, 165, 0),
    "棕色": (165, 42, 42),
    "银色": (192, 192, 192),
    "金色": (255, 215, 0),
}

VISION_PROMPT = (
    "你是失物招领图片识别助手。请识别图片中的物品，只输出 JSON，"
    "格式：{\"category\": \"...\", \"color\": \"...\", \"brand\": \"...\", \"description\": \"...\"}。"
    "可选类别：证件卡类、电子数码、钱包箱包、衣物饰品、书籍文具、钥匙、雨伞水杯、运动器材、宠物、其他。"
    "不确定的字段用 null。"
)


def _nearest_color(rgb: tuple[int, int, int]) -> str:
    """按欧氏距离把 RGB 归类到最近的常见颜色。"""
    best, best_dist = "其他", float("inf")
    for name, ref in NAMED_COLORS.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref))
        if dist < best_dist:
            best, best_dist = name, dist
    return best


def analyze_image_local(source: str | Path | bytes) -> dict:
    """本地图像分析：主色、亮度、构图与可读标签（无需外部服务）。"""
    from PIL import Image

    if isinstance(source, (bytes, bytearray)):
        img = Image.open(io.BytesIO(source)).convert("RGB")
    else:
        img = Image.open(source).convert("RGB")
    orig_w, orig_h = img.size
    img.thumbnail((64, 64))
    pixels = list(img.getdata())
    if not pixels:
        return {
            "color": None,
            "brightness": None,
            "dominant_rgb": None,
            "top_colors": [],
            "orientation": None,
            "aspect_ratio": None,
            "tags": [],
        }

    count = len(pixels)
    avg = tuple(round(sum(p[i] for p in pixels) / count) for i in range(3))
    color = _nearest_color(avg)
    brightness = round((0.299 * avg[0] + 0.587 * avg[1] + 0.114 * avg[2]) / 255, 2)

    # 主色聚类：按 48 级量化，取占比最高的前 3 组
    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    for p in pixels:
        key = (p[0] // 48, p[1] // 48, p[2] // 48)
        buckets.setdefault(key, []).append(p)
    top_groups = sorted(buckets.values(), key=len, reverse=True)[:3]
    top_colors = []
    for group in top_groups:
        gavg = tuple(round(sum(c[i] for c in group) / len(group)) for i in range(3))
        top_colors.append({
            "name": _nearest_color(gavg),
            "ratio": round(len(group) / count, 2),
        })

    # 构图
    ratio = round(orig_w / orig_h, 2) if orig_h else None
    if ratio is None:
        orientation = None
    elif ratio > 1.1:
        orientation = "横向"
    elif ratio < 0.9:
        orientation = "纵向"
    else:
        orientation = "方形"

    # 可读标签（用于前端展示的「识别结果」）
    tags: list[str] = []
    if brightness < 0.3:
        tags.append("深色系")
    elif brightness > 0.7:
        tags.append("浅色系")
    else:
        tags.append("中间调")
    r, g, b = avg
    if r > b + 20:
        tags.append("暖色调")
    elif b > r + 20:
        tags.append("冷色调")
    if color != "其他":
        tags.append(color)
    if orientation:
        tags.append(f"{orientation}构图")
    for item in top_colors[1:]:
        if item["name"] not in tags and item["name"] != "其他" and item["ratio"] >= 0.15:
            tags.append(f"{item['name']}点缀")

    return {
        "color": color,
        "brightness": brightness,
        "dominant_rgb": list(avg),
        "top_colors": top_colors,
        "orientation": orientation,
        "aspect_ratio": ratio,
        "tags": tags,
    }


def analyze_image_with_llm(image_bytes: bytes, content_type: str) -> dict | None:
    """调用视觉大模型识别物品；未配置 Key 或调用失败返回 None。"""
    if not settings.llm_api_key:
        return None
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    try:
        resp = httpx.post(
            f"{settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": VISION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{content_type or 'image/jpeg'};base64,{b64}"},
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
                "temperature": 0,
            },
            timeout=20.0,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return {
            "category": data.get("category"),
            "color": data.get("color"),
            "brand": data.get("brand"),
            "description": data.get("description"),
        }
    except Exception:
        return None


def analyze_image_file(path: str | Path, content_type: str | None = None) -> dict:
    """综合图像分析：优先视觉大模型，回退本地特征检测。"""
    local = analyze_image_local(path)
    if settings.llm_api_key:
        try:
            llm = analyze_image_with_llm(Path(path).read_bytes(), content_type or "image/jpeg")
            if llm and any(v for v in llm.values()):
                return {**local, **{k: v for k, v in llm.items() if v}, "source": "llm"}
        except Exception:
            pass
    return {**local, "source": "local"}


def analyze_image_bytes(content: bytes, content_type: str | None = None) -> dict:
    """与 analyze_image_file 相同，但输入为字节（用于数据库中存储的图片）。"""
    local = analyze_image_local(content)
    if settings.llm_api_key:
        try:
            llm = analyze_image_with_llm(content, content_type or "image/jpeg")
            if llm and any(v for v in llm.values()):
                return {**local, **{k: v for k, v in llm.items() if v}, "source": "llm"}
        except Exception:
            pass
    return {**local, "source": "local"}


def resolve_upload_path(url: str | None) -> Path | None:
    """把 /uploads/... 形式的图片 URL 解析为本地绝对路径。"""
    if not url or not url.startswith("/uploads/"):
        return None
    rel = url.removeprefix("/uploads/")
    return UPLOAD_DIR / rel
