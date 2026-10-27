"""认证接口：注册、登录、刷新令牌。"""

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.user_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
        user=user,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="用户注册")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册成功即自动登录，返回访问令牌与刷新令牌。"""
    user = register_user(db, data)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """支持用户名 / 邮箱 / 手机号登录。"""
    user = authenticate_user(db, data.account, data.password)
    return _token_response(user)


@router.post("/refresh", response_model=TokenResponse, summary="刷新访问令牌")
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """使用刷新令牌换取新的访问令牌（旋转刷新令牌）。"""
    try:
        payload = decode_refresh_token(data.refresh_token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")
    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return _token_response(user)
