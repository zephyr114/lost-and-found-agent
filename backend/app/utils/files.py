"""文件上传工具：校验并保存到本地 uploads 目录。"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def save_files(files: list[UploadFile], subdir: str = "misc") -> list[str]:
    """校验并保存上传的图片，返回可访问的 URL 列表。"""
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    urls: list[str] = []
    for file in files:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="存在空文件")
        if len(content) > max_bytes:
            raise HTTPException(status_code=400, detail=f"图片不能超过 {settings.max_upload_size_mb}MB")
        content_type = (file.content_type or "").split(";")[0].strip()
        ext = Path(file.filename or "").suffix.lower()
        if content_type not in ALLOWED_IMAGE_TYPES or (ext and ext not in ALLOWED_IMAGE_EXTS):
            raise HTTPException(status_code=400, detail="仅支持 jpg / png / webp / gif 图片")
        if not ext or ext not in ALLOWED_IMAGE_EXTS:
            ext = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }.get(content_type, ".jpg")

        now = datetime.now(timezone.utc)
        rel = Path(subdir) / f"{now.year:04d}" / f"{now.month:02d}" / f"{uuid.uuid4().hex}{ext}"
        dest = UPLOAD_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        urls.append(f"/uploads/{rel.as_posix()}")
    return urls
