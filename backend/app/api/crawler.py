"""
爬虫相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio

from app.database import get_db
from app.models import User, PlatformAccount, Job, Application, Resume, FilterRule
from app.utils.auth import get_current_user
from app.crawlers.boss import BossCrawler
from app.config import settings

router = APIRouter()


class LoginStatusResponse(BaseModel):
    platform: str
    status: str  # waiting_qrcode, logged_in, expired, error
    message: Optional[str] = None
    qrcode_url: Optional[str] = None


class SearchResult(BaseModel):
    jobs: List[dict]
    total: int
    message: str


class DeliveryResult(BaseModel):
    jobs_found: int
    jobs_applied: int
    jobs_filtered: int
    message: str


# 存储爬虫实例（简单实现，后续可用 Redis 优化）
_crawlers = {}


@router.post("/boss/login", response_model=LoginStatusResponse)
async def boss_login(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """启动 BOSS直聘登录流程"""
    crawler = BossCrawler()
    _crawlers[str(current_user.id)] = crawler

    # 启动登录流程
    try:
        # 获取二维码
        qrcode_path = await crawler.get_qrcode()

        return LoginStatusResponse(
            platform="boss",
            status="waiting_qrcode",
            message="请使用 BOSS直聘 App 扫码登录",
            qrcode_url=f"/api/crawler/boss/qrcode"
        )
    except Exception as e:
        return LoginStatusResponse(
            platform="boss",
            status="error",
            message=str(e)
        )


@router.get("/boss/qrcode")
async def get_boss_qrcode(
    current_user: User = Depends(get_current_user)
):
    """获取 BOSS直聘登录二维码图片"""
    crawler = _crawlers.get(str(current_user.id))
    if not crawler:
        raise HTTPException(status_code=400, detail="请先启动登录流程")

    from fastapi.responses import FileResponse
    qrcode_path = await crawler.get_qrcode()
    if qrcode_path:
        return FileResponse(qrcode_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="二维码未生成")


@router.get("/boss/login/status", response_model=LoginStatusResponse)
async def check_login_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查 BOSS直聘登录状态"""
    crawler = _crawlers.get(str(current_user.id))
    if not crawler:
        # 检查数据库中是否有保存的登录信息
        result = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.user_id == current_user.id,
                PlatformAccount.platform == "boss"
            )
        )
        account = result.scalar_one_or_none()
        if account and account.login_status == "active":
            return LoginStatusResponse(
                platform="boss",
                status="logged_in",
                message="账号已绑定"
            )
        return LoginStatusResponse(
            platform="boss",
            status="expired",
            message="请重新登录"
        )

    # 检查扫码状态
    logged_in = await crawler.check_login()
    if logged_in:
        # 保存 Cookie 到数据库
        cookies = await crawler.get_cookies()

        # 查找或创建账号记录
        result = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.user_id == current_user.id,
                PlatformAccount.platform == "boss"
            )
        )
        account = result.scalar_one_or_none()
        if account:
            account.cookies_encrypted = cookies
            account.login_status = "active"
            account.last_sync_at = datetime.utcnow()
        else:
            account = PlatformAccount(
                user_id=current_user.id,
                platform="boss",
                cookies_encrypted=cookies,
                login_status="active",
                last_sync_at=datetime.utcnow()
            )
            db.add(account)

        await db.commit()

        return LoginStatusResponse(
            platform="boss",
            status="logged_in",
            message="登录成功"
        )

    return LoginStatusResponse(
        platform="boss",
        status="waiting_qrcode",
        message="等待扫码..."
    )


@router.post("/boss/search", response_model=SearchResult)
async def boss_search(
    keywords: str,
    location: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索 BOSS直聘岗位"""
    # 检查账号绑定状态
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == "boss",
            PlatformAccount.login_status == "active"
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="请先绑定 BOSS直聘账号")

    # 创建爬虫实例并加载 Cookie
    crawler = BossCrawler()
    await crawler.load_cookies(account.cookies_encrypted)

    # 执行搜索
    jobs = await crawler.search_jobs(
        keywords=keywords,
        location=location,
        salary_min=salary_min,
        salary_max=salary_max,
        limit=limit
    )

    return SearchResult(
        jobs=jobs,
        total=len(jobs),
        message=f"找到 {len(jobs)} 个岗位"
    )


@router.post("/boss/delivery", response_model=DeliveryResult)
async def boss_delivery(
    rule_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """执行 BOSS直聘自动投递"""
    # 检查账号绑定
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == "boss",
            PlatformAccount.login_status == "active"
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="请先绑定 BOSS直聘账号")

    # 获取筛选规则
    result = await db.execute(
        select(FilterRule).where(
            FilterRule.id == rule_id,
            FilterRule.user_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="筛选规则不存在")

    # 获取默认简历
    result = await db.execute(
        select(Resume).where(
            Resume.user_id == current_user.id,
            Resume.is_default == True
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=400, detail="请先设置默认简历")

    # 在后台执行投递任务
    async def run_delivery():
        crawler = BossCrawler()
        await crawler.load_cookies(account.cookies_encrypted)

        # 搜索岗位
        keywords = " ".join(rule.skills_required) if rule.skills_required else ""
        jobs = await crawler.search_jobs(
            keywords=keywords,
            location=rule.locations[0] if rule.locations else None,
            salary_min=rule.salary_min,
            salary_max=rule.salary_max,
            limit=50
        )

        applied_count = 0
        filtered_count = 0

        for job_data in jobs:
            # 筛选检查
            if rule.keywords_exclude:
                title_lower = job_data.get("title", "").lower()
                if any(kw.lower() in title_lower for kw in rule.keywords_exclude):
                    filtered_count += 1
                    continue

            # 保存岗位
            job = Job(
                user_id=current_user.id,
                platform="boss",
                platform_job_id=job_data.get("job_id"),
                title=job_data.get("title"),
                company=job_data.get("company"),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                location=job_data.get("location"),
                jd_content=job_data.get("jd_content"),
                jd_url=job_data.get("url"),
                status="pending"
            )
            db.add(job)
            await db.flush()

            # 投递
            success = await crawler.apply_job(job_data.get("job_id"))
            if success:
                applied_count += 1
                job.status = "applied"
                job.applied_at = datetime.utcnow()

                # 记录投递
                application = Application(
                    user_id=current_user.id,
                    job_id=job.id,
                    resume_id=resume.id,
                    platform="boss",
                    status="applied"
                )
                db.add(application)

            await db.commit()

            # 控制间隔
            import random
            delay = random.uniform(settings.CRAWLER_DELAY_MIN, settings.CRAWLER_DELAY_MAX)
            await asyncio.sleep(delay)

            # 检查投递上限
            if applied_count >= settings.MAX_DAILY_APPLICATIONS:
                break

        await crawler.close()

    background_tasks.add_task(run_delivery)

    return DeliveryResult(
        jobs_found=50,
        jobs_applied=0,
        jobs_filtered=0,
        message="投递任务已启动，请在投递记录中查看进度"
    )


@router.post("/boss/apply/{job_id}")
async def boss_apply_single(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """单个岗位投递"""
    # 检查账号绑定
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == current_user.id,
            PlatformAccount.platform == "boss",
            PlatformAccount.login_status == "active"
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=400, detail="请先绑定 BOSS直聘账号")

    # 获取岗位信息
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 获取默认简历
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_default == True)
    )
    resume = result.scalar_one_or_none()

    # 执行投递
    crawler = BossCrawler()
    await crawler.load_cookies(account.cookies_encrypted)

    success = await crawler.apply_job(job.platform_job_id)
    await crawler.close()

    if success:
        job.status = "applied"
        job.applied_at = datetime.utcnow()

        if resume:
            application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume_id=resume.id,
                platform="boss",
                status="applied"
            )
            db.add(application)

        await db.commit()
        return {"message": "投递成功"}

    raise HTTPException(status_code=500, detail="投递失败")


crawler_router = router