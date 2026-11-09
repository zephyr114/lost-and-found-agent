"""智能 Agent 接口：图片识别、属性提取、对话式发布。"""

import time

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents import dialog, matching
from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.agent_log import AgentLog
from app.models.user import User
from app.utils.files import save_files
from app.utils.vision import analyze_image_file, resolve_upload_path

router = APIRouter(prefix="/agent", tags=["智能 Agent"])


class ExtractRequest(BaseModel):
    """AI 一键填充请求：用户粘贴一段物品描述。"""

    text: str = Field(min_length=2, max_length=2000)


class DialogRequest(BaseModel):
    """对话式发布：一轮用户输入 + 当前草稿。"""

    text: str = Field(default="", max_length=2000)
    draft: dict = Field(default_factory=dict)
    item_type: str = Field(default="lost", pattern="^(lost|found)$")


@router.post("/extract", summary="从描述文本提取物品属性（AI 一键填充）")
def extract_attributes(data: ExtractRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    started = time.perf_counter()
    attrs = matching.extract_item_attributes(data.text)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    db.add(
        AgentLog(
            user_id=user.id,
            task_type="attribute_extract",
            tool_name="extract_item_attributes",
            input_data={"text": data.text[:200]},
            tool_result=attrs,
            execution_time_ms=elapsed_ms,
            status="success",
        )
    )
    db.commit()
    return attrs


@router.post("/dialog", summary="对话式发布（多轮追问 + 自动填表）")
def dialog_publish(data: DialogRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """槽位填充式 Agent：合并用户输入，缺什么问什么，齐全后返回 done=True。"""
    started = time.perf_counter()
    result = dialog.dialog_step(data.text, data.draft, data.item_type)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    db.add(
        AgentLog(
            user_id=user.id,
            task_type="dialog_publish",
            tool_name="slot_filling_dialog",
            input_data={"text": data.text[:200], "item_type": data.item_type},
            tool_result={
                "missing": result["missing"],
                "done": result["done"],
                "next_field": result["next_field"],
            },
            execution_time_ms=elapsed_ms,
            status="success",
        )
    )
    db.commit()
    return result


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
