"""
API 路由模块
"""
from app.api.auth import router as auth_router
from app.api.resumes import router as resumes_router
from app.api.rules import router as rules_router
from app.api.applications import router as applications_router
from app.api.accounts import router as accounts_router
from app.api.jobs import router as jobs_router
from app.api.crawler import crawler_router

__all__ = [
    "auth_router",
    "resumes_router",
    "rules_router",
    "applications_router",
    "accounts_router",
    "jobs_router",
    "crawler_router"
]