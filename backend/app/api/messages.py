"""消息接口：收件箱、发件箱、未读数、已读、私信。"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.message import MessageListResponse, MessageOut, MessageSendRequest
from app.services import message_service

router = APIRouter(prefix="/messages", tags=["消息"])


@router.get("", response_model=MessageListResponse, summary="消息列表（inbox / sent）")
def list_messages(
    box: Literal["inbox", "sent"] = Query(default="inbox"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    return message_service.list_messages(db, user.id, box=box, skip=skip, limit=size)


@router.get("/unread-count", summary="未读消息数")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"count": message_service.unread_count(db, user.id)}


@router.put("/read-all", summary="全部标记为已读")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = message_service.mark_all_read(db, user.id)
    return {"message": f"已标记 {updated} 条消息为已读"}


@router.put("/{message_id}/read", response_model=MessageOut, summary="标记单条消息已读")
def mark_read(message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = message_service.get_message_or_404(db, message_id)
    msg = message_service.mark_read(db, msg, user.id)
    return message_service.serialize_message(msg, None)


@router.post("/send", response_model=MessageOut, status_code=201, summary="发送私信")
def send_message(data: MessageSendRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.receiver_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发消息")
    if db.get(User, data.receiver_id) is None:
        raise HTTPException(status_code=404, detail="收件人不存在")
    msg = message_service.create_message(db, data.receiver_id, data.content, message_type="user", sender_id=user.id)
    return message_service.serialize_message(msg, user.username)
