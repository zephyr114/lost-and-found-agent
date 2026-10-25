# 部署文档

## 方式一：本地开发（Windows / macOS / Linux）

### 环境要求

- Python ≥ 3.12
- Node.js ≥ 20（推荐 pnpm，也可用 npm）
- 可选：Docker（用于 MySQL / Redis / MinIO）

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows（macOS/Linux: source .venv/bin/activate）
pip install -r requirements.txt
copy .env.example .env          # 按需修改
uvicorn app.main:app --reload
```

- 接口：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health
- 首次启动自动建表并创建初始管理员（见 .env 的 `ADMIN_*`）

### 前端

```bash
cd frontend
pnpm install                    # 或 npm install
pnpm dev                        # 或 npm run dev
```

访问 http://localhost:5173 （开发代理已配置，无需处理跨域）。

### 数据库切换

开发默认 SQLite（`backend/lost_found.db`）。使用 MySQL：

```bash
docker compose -f docker/docker-compose.yml up -d mysql
# backend/.env 中设置：
DATABASE_URL=mysql+pymysql://laf_user:laf_pass@127.0.0.1:3306/lost_found?charset=utf8mb4
```

## 方式二：Docker Compose 一键部署

```bash
# 项目根目录
docker compose -f docker/docker-compose.yml up -d --build
```

服务清单：

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| frontend（Nginx） | 8080 | 前端页面 + 反向代理 |
| backend（uvicorn） | 8000 | API（/docs 查看接口） |
| mysql | 3306 | 业务数据（自动建库） |
| redis | 6379 | 预留 |
| minio | 9000/9001 | 预留（对象存储） |

首次访问前建议修改的环境变量（或直接编辑 compose 中的默认值）：

- `JWT_SECRET_KEY`：强随机密钥（`openssl rand -hex 32`）
- `ADMIN_PASSWORD`：初始管理员密码
- `MYSQL_PASSWORD`：数据库密码
- `LLM_API_KEY`：可选，配置后 Agent 属性提取调用大模型

## 生产部署要点（Linux + Nginx）

1. 后端：`uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4`（可用 systemd 托管）
2. 前端：`pnpm build` 后将 `dist/` 交给 Nginx；参考 `frontend/nginx.conf` 的代理配置
3. HTTPS：用 certbot 配置证书；把 `CORS_ORIGINS` 改为实际域名
4. 密钥管理：所有密钥只通过环境变量注入，不写入仓库（`.env` 已在 .gitignore）
5. 数据备份：定期备份 MySQL（mysqldump）与 `uploads/` 目录

## 持续集成（可选）

GitHub Actions 建议步骤：

1. `backend`：`pip install -r requirements.txt && pytest`
2. `frontend`：`pnpm install && pnpm run build`
3. 构建并推送 Docker 镜像到仓库，服务器端自动拉取更新
