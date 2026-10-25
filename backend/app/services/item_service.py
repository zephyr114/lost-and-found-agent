"""物品业务服务：发布、搜索、详情、编辑、删除、图片上传。"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate
from app.utils.geo import haversine_km

# 上传目录：backend/uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CATEGORIES = [
    "证件卡类", "电子数码", "钱包箱包", "衣物饰品", "书籍文具",
    "钥匙", "雨伞水杯", "运动器材", "宠物", "其他",
]


def get_categories() -> list[str]:
    """物品分类列表（供前端下拉使用）。"""
    return CATEGORIES


def get_item_or_404(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="物品不存在")
    return item


def serialize_item(item: Item, username: str | None = None) -> dict:
    out = {
        "id": item.id,
        "user_id": item.user_id,
        "item_type": item.item_type,
        "title": item.title,
        "category": item.category,
        "description": item.description,
        "color": item.color,
        "brand": item.brand,
        "location": item.location,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "event_time": item.event_time,
        "images": item.images or [],
        "status": item.status,
        "audit_status": item.audit_status,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "username": username,
    }
    return out


def create_item(db: Session, user: User, data: ItemCreate) -> Item:
    item = Item(
        user_id=user.id,
        item_type=data.item_type,
        title=data.title.strip(),
        category=data.category.strip(),
        description=data.description,
        color=data.color,
        brand=data.brand,
        location=data.location.strip(),
        latitude=data.latitude,
        longitude=data.longitude,
        event_time=data.event_time,
        images=[],
        status="active",
        audit_status="pending",  # 发布后进入审核状态
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_items(
    db: Session,
    *,
    q: str | None = None,
    item_type: str | None = None,
    category: str | None = None,
    location: str | None = None,
    status: str | None = None,
    audit_status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: str = "newest",
    lat: float | None = None,
    lng: float | None = None,
    skip: int = 0,
    limit: int = 20,
    mine: bool = False,
    viewer: User | None = None,
) -> dict:
    """按条件查询物品；公开列表默认仅展示已审核通过的物品。"""
    query = db.query(Item)

    if mine:
        if viewer is None:
            raise HTTPException(status_code=401, detail="请先登录")
        query = query.filter(Item.user_id == viewer.id)
    else:
        query = query.filter(Item.audit_status == (audit_status or "approved"))

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Item.title.like(like), Item.description.like(like), Item.brand.like(like))
        )
    if item_type:
        query = query.filter(Item.item_type == item_type)
    if category:
        query = query.filter(Item.category == category)
    if location:
        query = query.filter(Item.location.like(f"%{location}%"))
    if status:
        query = query.filter(Item.status == status)
    if date_from:
        query = query.filter(Item.event_time >= date_from)
    if date_to:
        query = query.filter(Item.event_time <= date_to)

    total = query.count()

    if sort == "oldest":
        query = query.order_by(Item.created_at.asc())
    elif sort == "distance" and lat is not None and lng is not None:
        # 距离排序在 Python 侧完成（数据量小；生产可下沉到 SQL）
        items = query.order_by(Item.created_at.desc()).all()
        items.sort(key=lambda it: haversine_km(lat, lng, it.latitude, it.longitude) or 1e9)
        return _build_page(db, items, total, skip, limit)
    else:
        query = query.order_by(Item.created_at.desc())

    items = query.offset(skip).limit(limit).all()
    return _build_page(db, items, total, skip, limit)


def _build_page(db: Session, items: list[Item], total: int, skip: int, limit: int) -> dict:
    user_ids = {it.user_id for it in items}
    usernames = dict(db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()) if user_ids else {}
    page_items = [serialize_item(it, usernames.get(it.user_id)) for it in items]
    return {"items": page_items, "total": total, "page": skip // limit + 1 if limit else 1, "size": limit}


def get_item_for_view(db: Session, item_id: int, viewer: User | None) -> dict:
    """详情查看：待审核物品仅发布者本人和管理员可见。"""
    item = get_item_or_404(db, item_id)
    if item.audit_status != "approved":
        if viewer is None or (viewer.id != item.user_id and viewer.role != "admin"):
            raise HTTPException(status_code=404, detail="物品不存在或尚未通过审核")
    owner = db.get(User, item.user_id)
    return serialize_item(item, owner.username if owner else None)


def update_item(db: Session, item: Item, data: ItemUpdate) -> Item:
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key in ("title", "category", "location") and isinstance(value, str):
            value = value.strip()
        setattr(item, key, value)
    # 内容修改后重新进入审核
    item.audit_status = "pending"
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: Item) -> None:
    db.delete(item)
    db.commit()


def save_images(db: Session, item: Item, files: list[UploadFile]) -> Item:
    """保存上传图片到本地 uploads 目录，返回更新后的物品。"""
    existing = len(item.images or [])
    if existing + len(files) > settings.max_images_per_item:
        raise HTTPException(status_code=400, detail=f"每个物品最多 {settings.max_images_per_item} 张图片")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    new_urls: list[str] = []
    for file in files:
        content = file.file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="存在空文件")
        if len(content) > max_bytes:
            raise HTTPException(status_code=400, detail=f"图片不能超过 {settings.max_upload_size_mb}MB")
        content_type = (file.content_type or "").split(";")[0].strip()
        ext = Path(file.filename or "").suffix.lower()
        if content_type not in ALLOWED_IMAGE_TYPES or (ext and ext not in ALLOWED_IMAGE_EXTS):
            raise HTTPException(status_code=400, detail="仅支持 jpg / png / webp / gif 图片")
        if not ext or ext not in ALLOWED_IMAGE_EXTS:
            ext = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }.get(content_type, ".jpg")

        now = datetime.now(timezone.utc)
        rel = Path(f"{now.year:04d}") / f"{now.month:02d}" / f"{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        new_urls.append(f"/uploads/{rel.as_posix()}")

    item.images = (item.images or []) + new_urls
    db.commit()
    db.refresh(item)
    return item


def remove_image(db: Session, item: Item, index: int) -> Item:
    images = item.images or []
    if index < 0 or index >= len(images):
        raise HTTPException(status_code=400, detail="图片序号无效")
    removed = images.pop(index)
    item.images = images
    db.commit()
    # 尽力删除本地文件（失败不影响业务）
    rel = removed.removeprefix("/uploads/")
    try:
        (UPLOAD_DIR / rel).unlink(missing_ok=True)
    except OSError:
        pass
    db.refresh(item)
    return item
