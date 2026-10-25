"""用户接口：个人资料与密码。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import PasswordChangeRequest, UserOut, UserUpdateRequest
from app.services.user_service import change_password, update_profile

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/me", response_model=UserOut, summary="获取当前用户资料")
def get_me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut, summary="修改个人资料")
def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_profile(db, user, data)


@router.put("/me/password", summary="修改密码")
def change_my_password(
    data: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(db, user, data)
    return {"message": "密码修改成功"}
