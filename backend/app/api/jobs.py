"""
岗位管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User, Job
from app.utils.auth import get_current_user

router = APIRouter()


class JobResponse(BaseModel):
    id: str
    platform: str
    platform_job_id: Optional[str]
    title: Optional[str]
    company: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    location: Optional[str]
    experience_required: Optional[str]
    education_required: Optional[str]
    jd_content: Optional[str]
    jd_url: Optional[str]
    status: str
    applied_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    items: List[JobResponse]


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取岗位列表"""
    query = select(Job).where(Job.user_id == current_user.id)

    if status:
        query = query.where(Job.status == status)
    if platform:
        query = query.where(Job.platform == platform)

    query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # 获取总数
    count_query = select(func.count(Job.id)).where(Job.user_id == current_user.id)
    if status:
        count_query = count_query.where(Job.status == status)
    if platform:
        count_query = count_query.where(Job.platform == platform)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return JobListResponse(
        total=total,
        items=[
            JobResponse(
                id=str(j.id),
                platform=j.platform,
                platform_job_id=j.platform_job_id,
                title=j.title,
                company=j.company,
                salary_min=j.salary_min,
                salary_max=j.salary_max,
                location=j.location,
                experience_required=j.experience_required,
                education_required=j.education_required,
                jd_content=j.jd_content,
                jd_url=j.jd_url,
                status=j.status,
                applied_at=j.applied_at,
                created_at=j.created_at
            ) for j in jobs
        ]
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个岗位详情"""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    return JobResponse(
        id=str(job.id),
        platform=job.platform,
        platform_job_id=job.platform_job_id,
        title=job.title,
        company=job.company,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        location=job.location,
        experience_required=job.experience_required,
        education_required=job.education_required,
        jd_content=job.jd_content,
        jd_url=job.jd_url,
        status=job.status,
        applied_at=job.applied_at,
        created_at=job.created_at
    )


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除岗位"""
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    await db.delete(job)
    await db.commit()

    return {"message": "删除成功"}