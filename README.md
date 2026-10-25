# 失物招领智能平台（Lost-and-Found Intelligent Platform）

支持失物发布、招领发布、智能匹配、消息沟通和管理员审核的失物招领网站。

**当前进度**：✅ 第一阶段（项目初始化） · ✅ 第二阶段（用户系统）

- 前后端项目骨架 + Git 仓库 + 环境变量配置
- 数据库连接（默认 SQLite 便于本地开发；MySQL 配置见 `docker/docker-compose.yml`）
- 后端 `GET /health` 健康检查接口
- 用户系统：注册 / 登录（用户名、邮箱、手机号）、JWT 鉴权、个人资料、修改密码、角色权限（user / admin）
- 前端：登录 / 注册 / 个人中心页面、路由守卫、管理员演示页

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Axios、ECharts |
| 后端 | Python、FastAPI、SQLAlchemy、Pydantic、JWT |
| 数据 | MySQL、Redis、MinIO、FAISS / Chroma（向量检索） |
| AI | 大语言模型、Embedding、LangGraph / LangChain、OCR、图像分析 |
| 部署 | Docker、Nginx、GitHub Actions |

## 目录结构

```text
lost-and-found-agent/
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── api/        # 路由（health 等）
│   │   ├── agents/     # 智能 Agent（第五阶段）
│   │   ├── services/   # 业务服务层
│   │   ├── models/     # ORM 模型
│   │   ├── schemas/    # Pydantic 模型
│   │   ├── repositories/ # 数据访问层
│   │   ├── database/   # 引擎与会话
│   │   ├── core/       # 配置
│   │   ├── utils/
│   │   └── main.py     # 应用入口
│   ├── tests/          # 测试
│   └── requirements.txt
├── frontend/           # Vue 3 前端
│   └── src/
│       ├── views/      # 页面
│       ├── components/ # 组件
│       ├── layouts/    # 布局
│       ├── stores/     # Pinia
│       ├── router/     # 路由
│       └── api/        # Axios 封装
├── knowledge_base/     # 知识库（第五阶段）
├── uploads/            # 本地文件存储（第三阶段）
├── docker/             # docker-compose（MySQL / Redis / MinIO）
└── docs/               # 项目文档（第七阶段完善）
```

## 快速启动

### 1. 后端（默认 8000 端口）

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows（Linux/macOS: source .venv/bin/activate）
pip install -r requirements.txt
copy .env.example .env        # 已提供 .env，可直接运行
uvicorn app.main:app --reload
```

验证：访问 http://127.0.0.1:8000/health ，应返回 `status: ok`、`database: connected`。
接口文档：启动后可访问 http://127.0.0.1:8000/docs （Swagger UI）。

### 初始管理员账号

首次启动后端会自动创建管理员（见 `backend/.env` 的 `ADMIN_*` 配置）：

```text
账号：admin
邮箱：admin@example.com
密码：admin123456   （仅开发环境！生产务必修改）
```

### 2. 前端（默认 5173 端口）

```bash
cd frontend
pnpm install    # 或 npm install
pnpm dev        # 或 npm run dev
```

验证：浏览器访问 http://localhost:5173 ，首页“系统状态”卡片显示后端与数据库状态。
开发环境请求经 Vite 代理转发到 8000 端口，无跨域问题。

### 3. 数据库

- 默认使用 SQLite（文件 `backend/lost_found.db`），开箱即用，适合无 MySQL 的本地环境。
- 使用 MySQL（需 Docker）：

  ```bash
  docker compose -f docker/docker-compose.yml up -d mysql
  ```

  然后在 `backend/.env` 中设置：

  ```text
  DATABASE_URL=mysql+pymysql://laf_user:laf_pass@127.0.0.1:3306/lost_found?charset=utf8mb4
  ```

## 测试

```bash
cd backend
.venv\Scripts\python -m pytest
```

当前 14 个用例覆盖：健康检查、注册（成功 / 重名 / 重邮箱 / 非法输入）、登录（三种账号方式 / 错误密码）、JWT 鉴权（无凭证 401 / 伪造凭证 401）、角色权限（普通用户 403 / 管理员 200）、个人资料修改、密码修改流程。

## 接口清单（第二阶段）

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/health` | 健康检查 | 公开 |
| POST | `/api/auth/register` | 注册（成功即自动登录） | 公开 |
| POST | `/api/auth/login` | 登录（用户名 / 邮箱 / 手机号） | 公开 |
| GET | `/api/users/me` | 获取当前用户资料 | 登录 |
| PUT | `/api/users/me` | 修改个人资料 | 登录 |
| PUT | `/api/users/me/password` | 修改密码 | 登录 |
| GET | `/api/admin/users` | 用户列表（演示） | 管理员 |

## 环境变量

- 后端：见 `backend/.env.example`（数据库连接、CORS 等）
- 前端：见 `frontend/.env.example`（`VITE_API_BASE_URL`）

约定：密钥、密码、Token 一律写入环境变量，不提交到代码仓库（`.env` 已在 .gitignore 中）。

## 阶段计划

1. ✅ 第一阶段：项目初始化
2. ✅ 第二阶段：用户系统（注册 / 登录 / JWT / 角色权限）
3. ⬜ 第三阶段：失物和招领功能
4. ⬜ 第四阶段：认领和消息功能
5. ⬜ 第五阶段：智能 Agent
6. ⬜ 第六阶段：管理后台
7. ⬜ 第七阶段：测试和部署
