"""
简历管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models import User, Resume
from app.utils.auth import get_current_user
from app.config import settings

router = APIRouter()


class ResumeResponse(BaseModel):
    id: str
    name: str
    file_type: Optional[str]
    tags: List[str]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    total: int
    items: List[ResumeResponse]


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取简历列表"""
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    return ResumeListResponse(
        total=len(resumes),
        items=[
            ResumeResponse(
                id=str(r.id),
                name=r.name,
                file_type=r.file_type,
                tags=r.tags or [],
                is_default=r.is_default,
                created_at=r.created_at
            ) for r in resumes
        ]
    )


@router.post("", response_model=ResumeResponse)
async def upload_resume(
    name: str = Form(...),
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    is_default: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传简历"""
    # 检查文件类型
    allowed_types = ["pdf", "doc", "docx"]
    file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持: {', '.join(allowed_types)}"
        )

    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)

    # 生成文件名
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)

    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 解析标签
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 如果设置为默认，先将其他简历的默认取消
    if is_default:
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id, Resume.is_default == True)
        )
        existing_default = result.scalars().all()
        for r in existing_default:
            r.is_default = False

    # 创建简历记录
    resume = Resume(
        user_id=current_user.id,
        name=name,
        file_path=file_path,
        file_type=file_ext,
        tags=tag_list,
        is_default=is_default
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeResponse(
        id=str(resume.id),
        name=resume.name,
        file_type=resume.file_type,
        tags=resume.tags or [],
        is_default=resume.is_default,
        created_at=resume.created_at
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除简历"""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 删除文件
    if resume.file_path and os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    # 删除数据库记录
    await db.delete(resume)
    await db.commit()

    return {"message": "删除成功"}


@router.put("/{resume_id}/default")
async def set_default_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """设置默认简历"""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 取消其他默认
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_default == True)
    )
    existing_defaults = result.scalars().all()
    for r in existing_defaults:
        r.is_default = False

    # 设置当前为默认
    resume.is_default = True
    await db.commit()

    return {"message": "已设置为默认简历"}