"""认证相关 Pydantic 模型。"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class RegisterRequest(BaseModel):
    """注册请求。"""

    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=6, max_length=72)


class LoginRequest(BaseModel):
    """登录请求：支持用户名 / 邮箱 / 手机号。"""

    account: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    """登录 / 注册成功响应。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    """刷新令牌请求。"""

    refresh_token: str = Field(min_length=10)
