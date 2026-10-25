"""消息业务服务：系统通知与用户私信。"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.user import User


def create_message(
    db: Session,
    receiver_id: int,
    content: str,
    message_type: str = "system",
    sender_id: int | None = None,
) -> Message:
    """创建消息并立即提交。"""
    msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=message_type,
        content=content,
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def serialize_message(msg: Message, sender_name: str | None = None) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": sender_name,
        "receiver_id": msg.receiver_id,
        "message_type": msg.message_type,
        "content": msg.content,
        "is_read": msg.is_read,
        "created_at": msg.created_at,
    }


def list_messages(
    db: Session,
    user_id: int,
    box: str = "inbox",
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """inbox=收到的消息，sent=发出的消息。"""
    query = db.query(Message)
    if box == "sent":
        query = query.filter(Message.sender_id == user_id)
    else:
        query = query.filter(Message.receiver_id == user_id)
    total = query.count()
    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

    sender_ids = {m.sender_id for m in messages if m.sender_id}
    names = dict(db.query(User.id, User.username).filter(User.id.in_(sender_ids)).all()) if sender_ids else {}
    items = [serialize_message(m, names.get(m.sender_id) if m.sender_id else "系统") for m in messages]
    return {"items": items, "total": total, "page": skip // limit + 1 if limit else 1, "size": limit}


def unread_count(db: Session, user_id: int) -> int:
    return db.query(Message).filter(Message.receiver_id == user_id, Message.is_read.is_(False)).count()


def get_message_or_404(db: Session, message_id: int) -> Message:
    msg = db.get(Message, message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return msg


def mark_read(db: Session, msg: Message, user_id: int) -> Message:
    if msg.receiver_id != user_id:
        raise HTTPException(status_code=403, detail="无权操作该消息")
    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg


def mark_all_read(db: Session, user_id: int) -> int:
    updated = (
        db.query(Message)
        .filter(Message.receiver_id == user_id, Message.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated
