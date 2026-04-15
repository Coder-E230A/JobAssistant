"""
筛选规则 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User, FilterRule
from app.utils.auth import get_current_user

router = APIRouter()


class RuleCreate(BaseModel):
    name: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    locations: Optional[List[str]] = []
    remote_accepted: bool = False
    skills_required: Optional[List[str]] = []
    keywords_include: Optional[List[str]] = []
    keywords_exclude: Optional[List[str]] = []


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    locations: Optional[List[str]] = None
    remote_accepted: Optional[bool] = None
    skills_required: Optional[List[str]] = None
    keywords_include: Optional[List[str]] = None
    keywords_exclude: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    id: str
    name: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    experience_min: Optional[int]
    experience_max: Optional[int]
    locations: List[str]
    remote_accepted: bool
    skills_required: List[str]
    keywords_include: List[str]
    keywords_exclude: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    total: int
    items: List[RuleResponse]


@router.get("", response_model=RuleListResponse)
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取筛选规则列表"""
    result = await db.execute(
        select(FilterRule).where(FilterRule.user_id == current_user.id).order_by(FilterRule.created_at.desc())
    )
    rules = result.scalars().all()
    return RuleListResponse(
        total=len(rules),
        items=[
            RuleResponse(
                id=str(r.id),
                name=r.name,
                salary_min=r.salary_min,
                salary_max=r.salary_max,
                experience_min=r.experience_min,
                experience_max=r.experience_max,
                locations=r.locations or [],
                remote_accepted=r.remote_accepted,
                skills_required=r.skills_required or [],
                keywords_include=r.keywords_include or [],
                keywords_exclude=r.keywords_exclude or [],
                is_active=r.is_active,
                created_at=r.created_at
            ) for r in rules
        ]
    )


@router.post("", response_model=RuleResponse)
async def create_rule(
    rule_data: RuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建筛选规则"""
    rule = FilterRule(
        user_id=current_user.id,
        name=rule_data.name,
        salary_min=rule_data.salary_min,
        salary_max=rule_data.salary_max,
        experience_min=rule_data.experience_min,
        experience_max=rule_data.experience_max,
        locations=rule_data.locations,
        remote_accepted=rule_data.remote_accepted,
        skills_required=rule_data.skills_required,
        keywords_include=rule_data.keywords_include,
        keywords_exclude=rule_data.keywords_exclude,
        is_active=True
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return RuleResponse(
        id=str(rule.id),
        name=rule.name,
        salary_min=rule.salary_min,
        salary_max=rule.salary_max,
        experience_min=rule.experience_min,
        experience_max=rule.experience_max,
        locations=rule.locations or [],
        remote_accepted=rule.remote_accepted,
        skills_required=rule.skills_required or [],
        keywords_include=rule.keywords_include or [],
        keywords_exclude=rule.keywords_exclude or [],
        is_active=rule.is_active,
        created_at=rule.created_at
    )


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    rule_data: RuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新筛选规则"""
    result = await db.execute(
        select(FilterRule).where(FilterRule.id == rule_id, FilterRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 更新字段
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    return RuleResponse(
        id=str(rule.id),
        name=rule.name,
        salary_min=rule.salary_min,
        salary_max=rule.salary_max,
        experience_min=rule.experience_min,
        experience_max=rule.experience_max,
        locations=rule.locations or [],
        remote_accepted=rule.remote_accepted,
        skills_required=rule.skills_required or [],
        keywords_include=rule.keywords_include or [],
        keywords_exclude=rule.keywords_exclude or [],
        is_active=rule.is_active,
        created_at=rule.created_at
    )


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除筛选规则"""
    result = await db.execute(
        select(FilterRule).where(FilterRule.id == rule_id, FilterRule.user_id == current_user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    await db.delete(rule)
    await db.commit()

    return {"message": "删除成功"}