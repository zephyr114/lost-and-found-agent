"""上传文件读取接口：从数据库流式返回图片。"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.stored_file import StoredFile

router = APIRouter(prefix="/files", tags=["文件"])


@router.get("/{file_id}", summary="读取上传的图片")
def read_file(file_id: str, db: Session = Depends(get_db)):
    record = db.get(StoredFile, file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    return Response(
        content=record.data,
        media_type=record.content_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
