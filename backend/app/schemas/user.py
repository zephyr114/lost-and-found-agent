"""用户相关 Pydantic 模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    """用户信息（响应模型，绝不含密码哈希）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    phone: str | None = None
    avatar: str | None = None
    credit_score: int
    role: str
    status: str
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """修改个人资料请求。"""

    username: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    avatar: str | None = Field(default=None, max_length=255)


class PasswordChangeRequest(BaseModel):
    """修改密码请求。"""

    old_password: str
    new_password: str = Field(min_length=6, max_length=72)
