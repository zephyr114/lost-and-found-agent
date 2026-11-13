"""文件上传工具：校验、压缩后存入数据库（Serverless 下不会丢图）。"""

import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.stored_file import StoredFile

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

_EXT_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

MAX_SIDE = 1600  # 长边最大像素，超过则等比缩小
JPEG_QUALITY = 82


def _normalize(content: bytes, filename: str, content_type: str) -> tuple[bytes, str, str]:
    """校验图片类型并压缩；返回（数据, Content-Type, 扩展名）。"""
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if not content:
        raise HTTPException(status_code=400, detail="存在空文件")
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"图片不能超过 {settings.max_upload_size_mb}MB")

    ct = (content_type or "").split(";")[0].strip().lower()
    ext = Path(filename or "").suffix.lower()
    if ct not in ALLOWED_IMAGE_TYPES or (ext and ext not in ALLOWED_IMAGE_EXTS):
        raise HTTPException(status_code=400, detail="仅支持 jpg / png / webp / gif 图片")
    if not ext or ext not in ALLOWED_IMAGE_EXTS:
        ext = _EXT_BY_TYPE.get(ct, ".jpg")

    # GIF 保留原样（保动画）；其余压缩为 JPEG，减小体积
    if ct == "image/gif":
        return content, ct, ext
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        img = img.convert("RGB")
        if max(img.size) > MAX_SIDE:
            img.thumbnail((MAX_SIDE, MAX_SIDE))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        data = buf.getvalue()
        if len(data) < len(content):
            return data, "image/jpeg", ".jpg"
    except Exception:
        pass
    return content, ct, ext


def _store(content: bytes, filename: str, content_type: str, db: Session, subdir: str) -> str:
    """把文件写入数据库，返回可访问 URL。"""
    data, ct, ext = _normalize(content, filename, content_type)
    file_id = uuid.uuid4().hex
    db.add(
        StoredFile(
            id=file_id,
            filename=f"{subdir}/{uuid.uuid4().hex}{ext}",
            content_type=ct,
            size=len(data),
            data=data,
        )
    )
    return f"/api/files/{file_id}"


def save_files(files: list[UploadFile], db: Session, subdir: str = "misc") -> list[str]:
    """批量保存上传图片，返回 URL 列表（提交事务由调用方或本函数统一完成）。"""
    urls = [
        _store(file.file.read(), file.filename or "", file.content_type or "", db, subdir)
        for file in files
    ]
    db.commit()
    return urls


def save_bytes(content: bytes, filename: str, content_type: str, db: Session, subdir: str = "misc") -> str:
    """保存单个文件的字节内容，返回 URL。"""
    url = _store(content, filename, content_type, db, subdir)
    db.commit()
    return url
