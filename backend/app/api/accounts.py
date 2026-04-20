"""
平台账号管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import User, PlatformAccount
from app.utils.auth import get_current_user

router = APIRouter()


class AccountResponse(BaseModel):
    id: str
    platform: str
    account_identifier: Optional[str]
    login_status: str
    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    total: int
    items: list[AccountResponse]


class CookieImportRequest(BaseModel):
    """Cookie导入请求"""
    cookies_json: str


class CookieImportResponse(BaseModel):
    """Cookie导入响应"""
    success: bool
    message: str
    account_id: Optional[str] = None


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取平台账号列表"""
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.user_id == current_user.id)
    )
    accounts = result.scalars().all()
    return AccountListResponse(
        total=len(accounts),
        items=[
            AccountResponse(
                id=str(a.id),
                platform=a.platform,
                account_identifier=a.account_identifier,
                login_status=a.login_status,
                last_sync_at=a.last_sync_at,
                created_at=a.created_at
            ) for a in accounts
        ]
    )


@router.get("/{platform}/status")
async def get_account_status(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定平台的账号状态"""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == platform
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return {"bound": False, "status": "not_bound"}

    return {
        "bound": True,
        "status": account.login_status,
        "last_sync": account.last_sync_at
    }


@router.post("/{platform}/import-cookies", response_model=CookieImportResponse)
async def import_cookies(
    platform: str,
    request: CookieImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    手动导入Cookie绑定账号

    当二维码登录失败时，用户可以手动从浏览器导出Cookie绑定账号

    Cookie格式示例：
    [
        {"name": "cookie_name", "value": "cookie_value", "domain": ".zhipin.com", "path": "/"}
    ]
    """
    import json

    # 验证Cookie格式
    try:
        cookies = json.loads(request.cookies_json)
        if not isinstance(cookies, list):
            return CookieImportResponse(
                success=False,
                message="Cookie格式错误：应为JSON数组"
            )

        # 验证每个Cookie项的基本字段
        for cookie in cookies:
            if not isinstance(cookie, dict):
                return CookieImportResponse(
                    success=False,
                    message="Cookie格式错误：每个项应为JSON对象"
                )
            if "name" not in cookie or "value" not in cookie:
                return CookieImportResponse(
                    success=False,
                    message="Cookie格式错误：缺少name或value字段"
                )

    except json.JSONDecodeError:
        return CookieImportResponse(
            success=False,
            message="Cookie格式错误：JSON解析失败"
        )

    # 查找或创建账号记录
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == platform
        )
    )
    account = result.scalar_one_or_none()

    if account:
        account.cookies_encrypted = request.cookies_json
        account.login_status = "active"
        account.last_sync_at = datetime.utcnow()
    else:
        account = PlatformAccount(
            user_id=current_user.id,
            platform=platform,
            cookies_encrypted=request.cookies_json,
            login_status="active",
            last_sync_at=datetime.utcnow()
        )
        db.add(account)

    await db.commit()
    await db.refresh(account)

    return CookieImportResponse(
        success=True,
        message="Cookie导入成功，账号已绑定",
        account_id=str(account.id)
    )


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """解绑平台账号"""
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == current_user.id
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    await db.delete(account)
    await db.commit()

    return {"message": "已解绑"}