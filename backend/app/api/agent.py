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


class PrecheckRequest(BaseModel):
    """发布前 AI 预审：标题 + 描述 + 地点。"""

    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=2000)
    location: str = Field(default="", max_length=100)


@router.post("/precheck", summary="发布前 AI 预审（风险与信息完整度）")
def precheck(data: PrecheckRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """规则审查：敏感词 / 联系方式 / 信息完整度，返回风险等级与建议。"""
    import re

    text = f"{data.title} {data.description} {data.location}"
    reasons: list[str] = []
    level = "low"
    score = 0

    hits = [w for w in matching.RISK_KEYWORDS if w in text]
    if hits:
        level = "high"
        score = max(score, 80)
        reasons.append(f"包含敏感词：{'、'.join(hits[:5])}，建议人工复核")

    phone = re.search(r"1[3-9]\d{9}", text)
    wechat = re.search(r"(微信|vx|VX|QQ|qq)[:：]?\s*[A-Za-z0-9_-]{5,}", text)
    if phone or wechat:
        if level != "high":
            level = "medium"
        score = max(score, 60)
        reasons.append("疑似包含联系方式，建议改为站内消息沟通，保护隐私")

    if len(data.description.strip()) < 10:
        score = max(score, 25)
        if level == "low":
            level = "medium"
        reasons.append("描述较短，补充颜色 / 品牌 / 特征可提升匹配率")
    if not data.location.strip():
        score = max(score, 20)
        reasons.append("未填写地点，可能影响匹配")

    if not reasons:
        reasons.append("信息完整，未发现明显风险")

    suggestion = {
        "high": "建议人工审核后再发布",
        "medium": "建议补充信息后发布",
        "low": "可以直接提交，审核通过后展示",
    }[level]

    db.add(
        AgentLog(
            user_id=user.id,
            task_type="risk_precheck",
            tool_name="precheck_item",
            input_data={"title": data.title[:100]},
            tool_result={"level": level, "score": score, "reasons": reasons},
            status="success",
        )
    )
    db.commit()
    return {"level": level, "score": score, "reasons": reasons, "suggestion": suggestion}


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
