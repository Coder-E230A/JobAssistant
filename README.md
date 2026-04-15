# JobAssistant - 简历筛选与自动投递工具

一款面向求职者的智能化招聘辅助工具，通过自动化技术帮助用户在多个招聘平台进行岗位筛选、简历匹配和自动投递，提升求职效率。

## 功能特性

### MVP 版本（当前）

- ✅ 用户注册/登录（JWT 认证）
- ✅ 简历管理（上传、多版本、标签）
- ✅ 筛选规则配置（薪资、地点、关键词）
- ✅ BOSS直聘平台接入
  - 扫码登录
  - 岗位搜索
  - 自动投递
- ✅ 投递记录跟踪与统计
- ✅ Web 界面操作

### 后续版本

- 🔄 AI 匹配度计算
- 🔄 多简历版本智能选择
- 🔄 定时自动投递
- 🔄 多平台支持（脉脉、猎聘、拉勾）
- 🔄 邮件通知
- 🔄 云端部署

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + Vite |
| 后端 | FastAPI (Python) |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 爬虫 | Playwright |
| 部署 | Docker + Docker Compose |

## 项目结构

```
JobAssistant/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # 状态管理 (Pinia)
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── backend/                  # 后端项目
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── models/          # 数据模型
│   │   ├── crawlers/        # 爬虫模块
│   │   ├── utils/           # 工具函数
│   │   ├── config.py        # 配置文件
│   │   ├── database.py      # 数据库连接
│   │   └── main.py          # 主应用
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml        # Docker 编排
├── PRD.md                    # 产品需求文档
└── README.md                 # 项目说明
```

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Node.js 18+ (本地开发)
- Python 3.11+ (本地开发)

### 使用 Docker Compose 启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

服务启动后：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 启动服务
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境配置

创建 `.env` 文件配置环境变量：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobassistant

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# 加密
ENCRYPTION_KEY=your-encryption-key-32-bytes-long

# 爬虫
PLAYWRIGHT_HEADLESS=false

# Redis
REDIS_URL=redis://localhost:6379/0
```

## 使用说明

### 1. 注册账号

访问 http://localhost:5173/register 注册账号

### 2. 绑定 BOSS直聘账号

1. 进入「平台账号」页面
2. 点击「绑定账号」
3. 使用 BOSS直聘 App 扫码登录

### 3. 上传简历

1. 进入「简历管理」页面
2. 上传 PDF/Word 格式简历
3. 设置为默认简历

### 4. 配置筛选规则

1. 进入「筛选规则」页面
2. 创建新规则
3. 设置薪资范围、目标城市、关键词等

### 5. 搜索和投递

- **手动搜索**：进入「岗位搜索」，输入关键词搜索，选择岗位投递
- **批量投递**：选择筛选规则，点击「开始投递」

## API 文档

启动后端服务后访问：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## 风险提示

⚠️ **重要提醒**

- 本工具仅供个人求职辅助使用
- 使用自动化工具可能违反招聘平台用户协议
- 用户需自行承担账号可能被封禁的风险
- 请控制投递频率，避免对平台造成过大压力

## 开发计划

详见 [PRD.md](./PRD.md)

## 许可证

MIT License