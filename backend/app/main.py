"""
JobAssistant 后端主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import auth, resumes, rules, applications, accounts, jobs
from app.api.crawler import crawler_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时清理资源


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端开发地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["简历"])
app.include_router(rules.router, prefix="/api/rules", tags=["筛选规则"])
app.include_router(applications.router, prefix="/api/applications", tags=["投递记录"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["平台账号"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["岗位"])
app.include_router(crawler_router, prefix="/api/crawler", tags=["爬虫"])


@app.get("/")
async def root():
    """根路由"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}