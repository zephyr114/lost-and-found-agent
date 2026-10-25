"""认证接口：注册、登录。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.user_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id, user.role), user=user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="用户注册")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册成功即自动登录，返回 JWT 与用户信息。"""
    user = register_user(db, data)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """支持用户名 / 邮箱 / 手机号登录。"""
    user = authenticate_user(db, data.account, data.password)
    return _token_response(user)
