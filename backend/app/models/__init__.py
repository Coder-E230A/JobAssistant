"""
JobAssistant 数据库模型
"""
from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联关系
    platform_accounts = relationship("PlatformAccount", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    filter_rules = relationship("FilterRule", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class PlatformAccount(Base):
    """招聘平台账号表"""
    __tablename__ = "platform_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # boss, maimai, liepin, lagou
    account_identifier = Column(String(255))  # 账号标识
    credentials_encrypted = Column(Text)  # 加密的登录凭证
    cookies_encrypted = Column(Text)  # 加密的 Cookie
    login_status = Column(String(20), default="active")  # active, expired, blocked
    last_sync_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="platform_accounts")


class Resume(Base):
    """简历表"""
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(20))  # pdf, doc, docx
    tags = Column(ARRAY(Text), default=[])  # 标签数组
    is_default = Column(Boolean, default=False)
    parsed_content = Column(JSONB)  # AI 解析后的结构化内容
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")


class FilterRule(Base):
    """筛选规则表"""
    __tablename__ = "filter_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    salary_min = Column(Integer)  # 最低薪资 (k)
    salary_max = Column(Integer)  # 最高薪资 (k)
    experience_min = Column(Integer)  # 最低工作年限
    experience_max = Column(Integer)  # 最高工作年限
    locations = Column(ARRAY(Text), default=[])  # 目标城市列表
    remote_accepted = Column(Boolean, default=False)  # 是否接受远程
    skills_required = Column(ARRAY(Text), default=[])  # 技能关键词
    industries = Column(ARRAY(Text), default=[])  # 行业方向
    company_scale = Column(ARRAY(Text), default=[])  # 公司规模要求
    keywords_include = Column(ARRAY(Text), default=[])  # 必须包含的关键词
    keywords_exclude = Column(ARRAY(Text), default=[])  # 排除的关键词
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="filter_rules")
    delivery_tasks = relationship("DeliveryTask", back_populates="rule")


class Job(Base):
    """岗位表"""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_job_id = Column(String(255))  # 平台岗位ID
    title = Column(String(500))
    company = Column(String(255))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    location = Column(String(255))
    experience_required = Column(String(100))
    education_required = Column(String(100))
    jd_content = Column(Text)  # JD 内容
    jd_url = Column(String(500))  # JD 链接
    match_score = Column(Integer)  # 匹配度分数
    status = Column(String(50), default="pending")  # pending, applied, viewed, interview, rejected
    applied_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    user = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


class Application(Base):
    """投递记录表"""
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"))
    platform = Column(String(50), nullable=False)
    status = Column(String(50), default="applied")  # applied, viewed, interview, rejected
    applied_at = Column(DateTime, server_default=func.now())
    response_at = Column(DateTime)  # 响应时间
    notes = Column(Text)  # 备注

    # 关联关系
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")


class DeliveryTask(Base):
    """投递任务表"""
    __tablename__ = "delivery_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("filter_rules.id"))
    scheduled_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    jobs_found = Column(Integer, default=0)  # 发现的岗位数
    jobs_applied = Column(Integer, default=0)  # 投递的岗位数
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    rule = relationship("FilterRule", back_populates="delivery_tasks")