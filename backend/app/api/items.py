"""物品接口：发布、列表、详情、编辑、删除、图片上传。"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.agents import matching
from app.api.deps import get_current_user, get_current_user_optional
from app.database.session import get_db
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemListResponse, ItemOut, ItemUpdate
from app.services import item_service

router = APIRouter(prefix="/items", tags=["物品"])


@router.post("", response_model=ItemOut, status_code=201, summary="发布失物 / 招领")
def create_item(
    data: ItemCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发布后进入待审核状态，审核通过后公开可见；同时后台运行智能匹配 Agent。"""
    item = item_service.create_item(db, user, data)
    # 发布后自动运行智能匹配（后台任务，不阻塞响应）
    background_tasks.add_task(matching.background_matching, item.id, user.id)
    return item_service.serialize_item(item, user.username)


@router.get("", response_model=ItemListResponse, summary="物品列表与搜索")
def list_items(
    q: str | None = Query(default=None, max_length=100, description="关键词（标题/描述/品牌）"),
    item_type: Literal["lost", "found"] | None = Query(default=None),
    category: str | None = Query(default=None),
    location: str | None = Query(default=None, description="地点关键词"),
    status: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: Literal["newest", "oldest", "distance"] = Query(default="newest"),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    mine: bool = Query(default=False, description="仅查看自己发布的物品"),
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_current_user_optional),
):
    skip = (page - 1) * size
    return item_service.list_items(
        db,
        q=q,
        item_type=item_type,
        category=category,
        location=location,
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        lat=lat,
        lng=lng,
        skip=skip,
        limit=size,
        mine=mine,
        viewer=viewer,
    )


@router.get("/categories", summary="物品分类列表")
def categories():
    return {"categories": item_service.get_categories()}


@router.get("/{item_id}", response_model=ItemOut, summary="物品详情")
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_current_user_optional),
):
    return item_service.get_item_for_view(db, item_id, viewer)


@router.put("/{item_id}", response_model=ItemOut, summary="编辑物品（发布者本人或管理员）")
def update_item(
    item_id: int,
    data: ItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    if item.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该物品")
    item = item_service.update_item(db, item, data)
    return item_service.serialize_item(item, user.username)


@router.delete("/{item_id}", summary="删除物品（发布者本人或管理员）")
def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    if item.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该物品")
    item_service.delete_item(db, item)
    return {"message": "删除成功"}


@router.post("/{item_id}/images", response_model=ItemOut, summary="上传物品图片")
def upload_images(
    item_id: int,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    if item.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作该物品")
    item = item_service.save_images(db, item, files)
    return item_service.serialize_item(item, user.username)


@router.delete("/{item_id}/images/{index}", response_model=ItemOut, summary="删除物品图片")
def delete_image(
    item_id: int,
    index: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    if item.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作该物品")
    item = item_service.remove_image(db, item, index)
    return item_service.serialize_item(item, user.username)
