"""
投递记录 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User, Application, Job, Resume
from app.utils.auth import get_current_user

router = APIRouter()


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    job_title: Optional[str]
    company: Optional[str]
    platform: str
    resume_id: Optional[str]
    resume_name: Optional[str]
    status: str
    applied_at: datetime
    response_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    total: int
    items: List[ApplicationResponse]


class StatsResponse(BaseModel):
    total_applied: int
    pending: int
    viewed: int
    interview: int
    rejected: int


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取投递记录列表"""
    query = select(Application).where(Application.user_id == current_user.id)

    if status:
        query = query.where(Application.status == status)
    if platform:
        query = query.where(Application.platform == platform)

    query = query.order_by(Application.applied_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    applications = result.scalars().all()

    # 获取总数
    count_query = select(func.count(Application.id)).where(Application.user_id == current_user.id)
    if status:
        count_query = count_query.where(Application.status == status)
    if platform:
        count_query = count_query.where(Application.platform == platform)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    items = []
    for app in applications:
        # 获取岗位信息
        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one_or_none()

        # 获取简历信息
        resume_name = None
        if app.resume_id:
            resume_result = await db.execute(select(Resume).where(Resume.id == app.resume_id))
            resume = resume_result.scalar_one_or_none()
            resume_name = resume.name if resume else None

        items.append(ApplicationResponse(
            id=str(app.id),
            job_id=str(app.job_id),
            job_title=job.title if job else None,
            company=job.company if job else None,
            platform=app.platform,
            resume_id=str(app.resume_id) if app.resume_id else None,
            resume_name=resume_name,
            status=app.status,
            applied_at=app.applied_at,
            response_at=app.response_at,
            notes=app.notes
        ))

    return ApplicationListResponse(total=total, items=items)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取投递统计"""
    # 统计各状态数量
    result = await db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    )
    status_counts = result.all()

    counts = {"applied": 0, "viewed": 0, "interview": 0, "rejected": 0}
    for status, count in status_counts:
        counts[status] = count

    return StatsResponse(
        total_applied=sum(counts.values()),
        pending=counts.get("applied", 0),
        viewed=counts.get("viewed", 0),
        interview=counts.get("interview", 0),
        rejected=counts.get("rejected", 0)
    )


@router.put("/{application_id}/status")
async def update_status(
    application_id: str,
    status: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新投递状态"""
    valid_statuses = ["applied", "viewed", "interview", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效的状态，仅支持: {', '.join(valid_statuses)}")

    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="投递记录不存在")

    application.status = status
    if notes:
        application.notes = notes
    if status in ["viewed", "interview", "rejected"]:
        application.response_at = datetime.utcnow()

    await db.commit()

    return {"message": "状态已更新"}