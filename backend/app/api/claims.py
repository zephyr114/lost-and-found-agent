"""认领接口：提交申请、我的申请、收到的申请、审核处理。"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.claim import ClaimListResponse, ClaimOut, ClaimReviewRequest
from app.services import claim_service, item_service
from app.utils.files import save_files

router = APIRouter(tags=["认领"])


@router.post("/items/{item_id}/claims", response_model=ClaimOut, status_code=201, summary="提交认领申请")
def create_claim(
    item_id: int,
    proof_description: Annotated[str, Form(min_length=1, max_length=2000)],
    contact: Annotated[str | None, Form(max_length=100)] = None,
    files: list[UploadFile] = File(default=[]),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item_service.get_item_or_404(db, item_id)
    urls = save_files(files, subdir="claims") if files else []
    claim = claim_service.create_claim(db, item, user, proof_description, contact, urls)
    return claim_service.serialize_claim(db, claim)


@router.get("/claims/my", response_model=ClaimListResponse, summary="我的认领申请")
def my_claims(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    return claim_service.list_my_claims(db, user.id, skip=skip, limit=size)


@router.get("/claims/received", response_model=ClaimListResponse, summary="收到我物品的认领申请")
def received_claims(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    return claim_service.list_received_claims(db, user.id, skip=skip, limit=size)


@router.post("/claims/{claim_id}/images", response_model=ClaimOut, summary="补充认领证明材料")
def add_claim_images(
    claim_id: int,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claim_service.get_claim_or_404(db, claim_id)
    urls = save_files(files, subdir="claims")
    claim = claim_service.add_proof_images(db, claim, user, urls)
    return claim_service.serialize_claim(db, claim)


@router.put("/claims/{claim_id}/approve", response_model=ClaimOut, summary="同意认领（物品发布者）")
def approve(
    claim_id: int,
    data: ClaimReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claim_service.get_claim_or_404(db, claim_id)
    claim = claim_service.approve_claim(db, claim, user, data.review_comment)
    return claim_service.serialize_claim(db, claim)


@router.put("/claims/{claim_id}/reject", response_model=ClaimOut, summary="拒绝认领（物品发布者）")
def reject(
    claim_id: int,
    data: ClaimReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claim_service.get_claim_or_404(db, claim_id)
    claim = claim_service.reject_claim(db, claim, user, data.review_comment)
    return claim_service.serialize_claim(db, claim)


@router.put("/claims/{claim_id}/request-proof", response_model=ClaimOut, summary="要求补充证明（物品发布者）")
def request_proof(
    claim_id: int,
    data: ClaimReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claim_service.get_claim_or_404(db, claim_id)
    claim = claim_service.request_proof(db, claim, user, data.review_comment)
    return claim_service.serialize_claim(db, claim)


@router.delete("/claims/{claim_id}", response_model=ClaimOut, summary="撤回认领申请（申请人）")
def cancel(
    claim_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    claim = claim_service.get_claim_or_404(db, claim_id)
    claim = claim_service.cancel_claim(db, claim, user)
    return claim_service.serialize_claim(db, claim)
