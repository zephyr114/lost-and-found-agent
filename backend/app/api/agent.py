"""智能 Agent 接口：图片识别。"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.agent_log import AgentLog
from app.models.user import User
from app.utils.files import save_files
from app.utils.vision import analyze_image_file, resolve_upload_path

router = APIRouter(prefix="/agent", tags=["智能 Agent"])


@router.post("/analyze-image", summary="图片识别（上传图片，返回颜色 / 亮度等特征）")
def analyze_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    urls = save_files([file], subdir="analysis")
    path = resolve_upload_path(urls[0])
    result = analyze_image_file(path, file.content_type) if path else {}

    db.add(
        AgentLog(
            user_id=user.id,
            task_type="image_recognition",
            tool_name="analyze_image",
            input_data={"image_url": urls[0]},
            tool_result=result,
            status="success",
        )
    )
    db.commit()
    return {"image_url": urls[0], **result}
