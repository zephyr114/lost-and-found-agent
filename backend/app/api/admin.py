"""管理接口（第二阶段仅用户列表，用于验证角色权限；完整后台见第六阶段）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.database.session import get_db
from app.schemas.user import UserOut
from app.services.user_service import list_users

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/users", response_model=list[UserOut], summary="用户列表（仅管理员）")
def admin_list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    _: object = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_users(db, skip=skip, limit=limit)
