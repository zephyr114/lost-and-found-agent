"""用户业务服务：注册、认证、资料维护。"""

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import PasswordChangeRequest, UserUpdateRequest


def _check_unique(
    db: Session,
    username: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    exclude_id: int | None = None,
) -> None:
    """检查用户名 / 邮箱 / 手机号是否已被占用（可排除自身）。"""
    conditions = []
    if username:
        conditions.append(User.username == username)
    if email:
        conditions.append(User.email == email)
    if phone:
        conditions.append(User.phone == phone)
    if not conditions:
        return
    dup = db.query(User).filter(or_(*conditions)).first()
    if dup is None or dup.id == exclude_id:
        return
    if username and dup.username == username:
        raise HTTPException(status_code=409, detail="用户名已被注册")
    if email and dup.email == email:
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    if phone and dup.phone == phone:
        raise HTTPException(status_code=409, detail="手机号已被注册")


def register_user(db: Session, data: RegisterRequest) -> User:
    """创建新用户，用户名 / 邮箱 / 手机号冲突返回 409。"""
    _check_unique(db, username=data.username, email=data.email, phone=data.phone or None)
    user = User(
        username=data.username,
        email=data.email,
        phone=data.phone or None,
        password_hash=hash_password(data.password),
        role="user",
        status="active",
        credit_score=100,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, account: str, password: str) -> User:
    """按用户名 / 邮箱 / 手机号登录，失败返回 401，禁用返回 403。"""
    user = (
        db.query(User)
        .filter(or_(User.username == account, User.email == account, User.phone == account))
        .first()
    )
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    return user


def update_profile(db: Session, user: User, data: UserUpdateRequest) -> User:
    """更新个人资料（仅更新传入字段），冲突返回 409。"""
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    if "phone" in updates and not updates["phone"]:
        updates["phone"] = None
    if not updates:
        return user
    _check_unique(
        db,
        username=updates.get("username"),
        email=updates.get("email"),
        phone=updates.get("phone"),
        exclude_id=user.id,
    )
    for key, value in updates.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: PasswordChangeRequest) -> None:
    """修改密码：先校验原密码。"""
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    user.password_hash = hash_password(data.new_password)
    db.commit()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """用户列表（管理端使用）。"""
    return db.query(User).order_by(User.id).offset(skip).limit(limit).all()
