"""
JobAssistant 后端配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "JobAssistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobassistant"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 加密配置
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-long"

    # 文件存储配置
    UPLOAD_DIR: str = "./uploads/resumes"

    # 爬虫配置
    PLAYWRIGHT_HEADLESS: bool = False  # MVP阶段使用有头模式方便调试
    CRAWLER_DELAY_MIN: float = 3.0
    CRAWLER_DELAY_MAX: float = 10.0
    MAX_DAILY_APPLICATIONS: int = 50

    # Redis 配置 (第二阶段使用)
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()