# 失物招领智能平台（Lost-and-Found Intelligent Platform）

<!-- 徽章：CI 状态徽章在启用 GitHub Actions 后取消下面这行注释即可 -->
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
<!-- [![CI](https://github.com/zephyr114/lost-and-found-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/zephyr114/lost-and-found-agent/actions) -->

支持失物发布、招领发布、智能匹配、消息沟通和管理员审核的失物招领网站。

**当前进度**：✅ 全部七个阶段完成 + 🖼️ 图片识别（主色/亮度检测 + 可选视觉大模型）

## 功能总览

| 模块 | 能力 |
| --- | --- |
| 用户系统 | 注册（邮箱/手机号）、登录（用户名/邮箱/手机号）、JWT 认证、资料修改、改密、角色权限（user/admin）、信用分、账号禁用 |
| 失物招领 | 发布失物/招领、审核流、关键词/类别/地点/时间筛选、距离排序、详情、编辑、删除、图片上传（≤6 张、≤5MB/张） |
| 认领消息 | 认领申请（特征说明+证明图片）、同意/拒绝/要求补充证明、自动拒绝其余申请、站内私信、系统通知、未读角标 |
| 智能 Agent | 属性提取（规则引擎+可选 LLM）、相似搜索、多维打分（类别/名称/颜色/品牌/时间/距离/特征）、中文匹配理由、自动通知、风险词转人工审核、工具级执行日志 |
| 图片识别 | 物品图片主色 / 亮度检测（本地 Pillow，零依赖）、自动补充物品颜色；配置视觉大模型后识别类别 / 颜色 / 品牌 / 描述 |
| 管理后台 | ECharts 数据统计、信息审核、用户管理、认领总览、举报处理、系统公告、Agent 日志、操作审计日志 |
| 安全 | bcrypt 密码哈希、JWT（环境变量密钥）、三级权限依赖、前端路由守卫、上传校验、敏感配置不入库 |

## 技术栈

- **前端**：Vue 3 · TypeScript · Vite · Element Plus · Pinia · Vue Router · Axios · ECharts
- **后端**：Python 3.12 · FastAPI · SQLAlchemy 2 · Pydantic v2 · PyJWT · bcrypt
- **数据**：MySQL 8（生产）/ SQLite（开发）· Redis / MinIO（Docker Compose 预留）
- **AI**：DeepSeek 等 OpenAI 兼容接口（可选，不配置则使用内置规则引擎）
- **部署**：Docker · Docker Compose · Nginx

## 快速启动

### 后端（默认 8000 端口）

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows（macOS/Linux: source .venv/bin/activate）
pip install -r requirements.txt
copy .env.example .env          # 按需修改
uvicorn app.main:app --reload
```

验证：http://127.0.0.1:8000/health 返回 `{"status":"ok","database":"connected"}`；接口文档 http://127.0.0.1:8000/docs

### 前端（默认 5173 端口）

```bash
cd frontend
pnpm install                    # 或 npm install
pnpm dev                        # 或 npm run dev
```

浏览器打开 http://localhost:5173 （开发代理已配置，无跨域问题）

### 一键部署到云端（推荐，永久在线）

**Render（免费 PostgreSQL + 两个服务，点一下即可）：**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/zephyr114/lost-and-found-agent)

点击后登录 Render → 确认 Blueprint 配置（`render.yaml` 会自动创建数据库/后端/前端）→ Apply，几分钟后即可在 `https://frontend.onrender.com` 访问。

> **自定义域名**：部署完成后在 Render 控制台 → 前端服务 → Settings → Custom Domain 添加你购买的域名（需在域名注册商处把 CNAME 指向 Render 提供的地址）。免费子域名 `*.onrender.com` 可先直接使用。

**Railway（支持 MySQL）**：见 [docs/github-and-deploy.md](docs/github-and-deploy.md)。

### 一键部署（Docker Compose，自建服务器）

```bash
docker compose -f docker/docker-compose.yml up -d --build
# 前端 http://localhost:8080，后端 http://localhost:8000/docs
```

生产环境请修改 `JWT_SECRET_KEY`、`ADMIN_PASSWORD`、`MYSQL_PASSWORD`（详见 docs/deployment.md）。

## 演示账号

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| admin（admin@example.com） | admin123456 | 管理员 |
| demo_user1 / demo_user2 / demo_user3 | demo123456 | 普通用户 |

演示数据（示例失物/招领/认领申请/公告，含智能匹配结果）：

```bash
cd backend
.venv\Scripts\python scripts\seed_demo.py
```

## 测试

```bash
cd backend
.venv\Scripts\python -m pytest     # 64 个用例：健康检查/认证/权限/物品/认领/消息/Agent/管理后台/图片识别
```

覆盖：注册重名 409、错误密码 401、无凭证 401、越权 403、待审核隐藏、图片类型校验、认领全流程状态机、自动拒绝并发申请、消息已读、匹配打分与阈值、举报处理、公告 CRUD、操作与 Agent 日志等。

前端：`cd frontend && pnpm run build`（vue-tsc 类型检查 + 生产构建）。

## 环境变量

- 后端：`backend/.env.example`（数据库、JWT、初始管理员、上传、LLM 配置）
- 前端：`frontend/.env.example`（`VITE_API_BASE_URL`）

约定：密钥、密码、Token 一律放环境变量，绝不写入代码仓库（`.env` 已忽略）。

## 目录结构

```text
lost-and-found-agent/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由（auth/users/items/claims/messages/matches/reports/announcements/admin）
│   │   ├── agents/         # 智能匹配 Agent（matching.py 工具链）
│   │   ├── services/       # 业务服务层
│   │   ├── models/         # ORM 模型（users/items/claims/messages/matches/reports/announcements/agent_logs/operation_logs）
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── database/       # 引擎与会话
│   │   ├── core/           # 配置 / 安全
│   │   ├── utils/          # 地理距离 / 文件上传
│   │   └── main.py
│   ├── scripts/seed_demo.py  # 演示数据
│   ├── tests/              # 58 个测试用例
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 用户端页面 + admin/ 管理后台页面
│   │   ├── layouts/        # AdminLayout 等布局
│   │   ├── components/     # ItemCard 等组件
│   │   ├── stores/         # Pinia（user/app）
│   │   ├── router/         # 路由与守卫
│   │   └── api/            # Axios 封装
│   ├── Dockerfile · nginx.conf
│   └── package.json
├── docker/docker-compose.yml  # 完整部署（mysql/redis/minio/backend/frontend）
├── docs/                   # requirements / architecture / api / deployment
├── knowledge_base/         # 知识库
└── uploads/                # 本地文件（生产可切 MinIO）
```

## 文档

- [需求文档](docs/requirements.md) · [架构文档](docs/architecture.md) · [API 文档](docs/api.md) · [部署文档](docs/deployment.md) · [GitHub 发布与在线部署指南](docs/github-and-deploy.md)

## 阶段计划

1. ✅ 项目初始化（骨架 / Git / 数据库连接 / /health / 首页）
2. ✅ 用户系统（注册 / 登录 / JWT / 角色权限）
3. ✅ 失物和招领（发布 / 搜索 / 详情 / 图片 / 编辑删除）
4. ✅ 认领和消息（申请 / 审核 / 状态流转 / 站内消息）
5. ✅ 智能 Agent（属性提取 / 匹配打分 / 原因解释 / 自动通知 / 执行日志）
6. ✅ 管理后台（统计 / 审核 / 用户 / 举报 / 公告 / 日志）
7. ✅ 测试和部署（58 用例 / Docker / 文档 / 演示数据）

## 验收指标对照

- 注册/发布成功率 ≥99%、图片上传 ≥95%：全部核心路径有自动化测试覆盖
- 搜索响应 ≤2s、智能匹配 ≤5s：本机 SQLite 实测均为毫秒级
- 匹配结果可解释：每条匹配附中文理由列表
- 管理员可完成完整审核流程：信息审核 / 举报 / 用户禁用均有接口与页面
- 核心接口错误处理：400/401/403/404/409/422 语义清晰
- 一键启动：`docker compose up -d --build`
- README 完整：本文档 + docs/ 四份文档
