"""
简历管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import subprocess
from datetime import datetime

import pdfplumber
from docx import Document
from pdf2image import convert_from_path

from app.database import get_db
from app.models import User, Resume
from app.utils.auth import get_current_user, get_user_by_token
from app.config import settings

router = APIRouter()

# 预览图片存储目录
PREVIEW_DIR = os.path.join(settings.UPLOAD_DIR, "previews")


def ensure_preview_dir():
    """确保预览目录存在"""
    if not os.path.exists(PREVIEW_DIR):
        os.makedirs(PREVIEW_DIR)


def convert_pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    将 PDF 文件转换为图片

    返回图片文件路径列表（每页一张图片）
    """
    try:
        # 将 PDF 每页转换为图片
        images = convert_from_path(pdf_path, dpi=150)

        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(output_dir, f"page_{i+1}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)

        return image_paths
    except Exception as e:
        raise RuntimeError(f"PDF 转图片失败: {str(e)}")


def convert_word_to_pdf(word_path: str, output_dir: str) -> str:
    """
    使用 LibreOffice 将 Word 文件转换为 PDF

    返回转换后的 PDF 文件路径
    """
    try:
        # 使用 LibreOffice 转换
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                word_path
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

        # 获取生成的 PDF 文件名
        base_name = os.path.splitext(os.path.basename(word_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        if not os.path.exists(pdf_path):
            raise RuntimeError("转换后的 PDF 文件不存在")

        return pdf_path
    except subprocess.TimeoutExpired:
        raise RuntimeError("LibreOffice 转换超时")
    except FileNotFoundError:
        raise RuntimeError("LibreOffice 未安装")
    except Exception as e:
        raise RuntimeError(f"Word 转 PDF 失败: {str(e)}")


def generate_preview_images(file_path: str, file_type: str, resume_id: str) -> List[str]:
    """
    生成简历预览图片

    根据文件类型转换为图片，返回图片路径列表
    """
    ensure_preview_dir()

    # 为每个简历创建独立的预览目录
    preview_subdir = os.path.join(PREVIEW_DIR, resume_id)
    if not os.path.exists(preview_subdir):
        os.makedirs(preview_subdir)

    # 清理旧的预览图片
    for old_file in os.listdir(preview_subdir):
        old_path = os.path.join(preview_subdir, old_file)
        if os.path.isfile(old_path):
            os.remove(old_path)

    try:
        if file_type == "pdf":
            # 直接将 PDF 转换为图片
            return convert_pdf_to_images(file_path, preview_subdir)

        elif file_type in ["doc", "docx"]:
            # 先将 Word 转换为 PDF，再转换为图片
            pdf_path = convert_word_to_pdf(file_path, preview_subdir)
            images = convert_pdf_to_images(pdf_path, preview_subdir)
            # 删除中间生成的 PDF 文件
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return images

        else:
            raise RuntimeError(f"不支持的文件类型: {file_type}")

    except Exception as e:
        raise RuntimeError(f"生成预览图片失败: {str(e)}")


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


@router.get("/{resume_id}/preview")
async def get_resume_preview(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取简历预览图片列表

    将 PDF/Word 文件转换为图片，返回图片列表信息
    用于完全呈现文件的格式和内容
    """
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="简历文件不存在")

    try:
        # 生成预览图片
        image_paths = generate_preview_images(
            resume.file_path,
            resume.file_type,
            str(resume.id)
        )

        # 返回图片信息列表
        pages = []
        for i, path in enumerate(image_paths):
            pages.append({
                "page_number": i + 1,
                "image_url": f"/api/resumes/{resume_id}/preview/{i + 1}",
                "total_pages": len(image_paths)
            })

        return {
            "resume_name": resume.name,
            "file_type": resume.file_type,
            "total_pages": len(image_paths),
            "pages": pages
        }

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resume_id}/preview/{page_number}")
async def get_resume_preview_page(
    resume_id: str,
    page_number: int,
    current_user: User = Depends(get_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    获取简历预览的指定页图片

    返回 PNG 图片文件
    使用 token 查询参数认证，便于图片直接显示
    """
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 查找预览图片
    preview_subdir = os.path.join(PREVIEW_DIR, resume_id)
    image_path = os.path.join(preview_subdir, f"page_{page_number}.png")

    if not os.path.exists(image_path):
        # 如果图片不存在，尝试重新生成
        if resume.file_path and os.path.exists(resume.file_path):
            try:
                generate_preview_images(
                    resume.file_path,
                    resume.file_type,
                    resume_id
                )
            except RuntimeError:
                raise HTTPException(status_code=500, detail="生成预览图片失败")
        else:
            raise HTTPException(status_code=404, detail="简历文件不存在")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="预览图片不存在")

    return FileResponse(image_path, media_type="image/png")


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: User = Depends(get_user_by_token),
    db: AsyncSession = Depends(get_db)
):
    """
    下载简历文件

    返回原始简历文件（PDF/Word）
    使用 token 查询参数认证，便于直接下载
    """
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="简历文件不存在")

    # 根据文件类型设置媒体类型
    media_type_map = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
    media_type = media_type_map.get(resume.file_type or "", "application/octet-stream")

    return FileResponse(
        path=resume.file_path,
        media_type=media_type,
        filename=f"{resume.name}.{resume.file_type}"
    )