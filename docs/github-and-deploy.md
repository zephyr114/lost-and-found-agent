# GitHub 发布与在线部署指南

> 本文档指导你将本项目发布到 GitHub 并实现永久在线部署。
> 发布到 GitHub 和部署到云平台都需要**你自己的账号授权**（GitHub 账号 + 云平台账号）。

## 一、发布到 GitHub

### 前置准备

1. 注册 GitHub 账号：https://github.com
2. 本机已安装 git（项目已在本地用 git 管理，8+ 个提交）

### 方式 A：使用 GitHub CLI（推荐，最简单）

```bash
# 安装 gh 后登录
gh auth login

# 在项目根目录创建远程仓库并推送
cd lost-and-found-agent
gh repo create lost-and-found-agent --public --source=. --remote=origin --push
```

### 方式 B：手动推送（网页创建 + git 命令）

1. 在 GitHub 网页点击 **New repository**，创建空仓库（建议 Public，名称如 `lost-and-found-agent`，**不要**勾选初始化 README）
2. 配置身份并推送：

```bash
cd lost-and-found-agent

git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

git remote add origin https://github.com/你的用户名/lost-and-found-agent.git
git branch -M main
git push -u origin main
```

3. 推送时输入 GitHub 用户名 + **Personal Access Token**（Settings → Developer settings → Personal access tokens，勾选 `repo` 权限）作为密码

推送成功后，GitHub Actions 的 CI（`.github/workflows/ci.yml`）会自动运行后端测试和前端构建。

## 二、永久在线部署

项目已内置完整 Docker 配置（`docker/docker-compose.yml`：MySQL + Redis + MinIO + 后端 + 前端 + Nginx）。选择以下任一方案：

### 方案 A：Railway（推荐，支持 MySQL，最省心）

1. 注册 https://railway.app 并用 GitHub 授权
2. New Project → **Deploy from GitHub repo** 选择本项目
3. 添加 MySQL：项目内 **New → Database → MySQL**，Railway 会自动注入 `MYSQL_URL` 等变量
4. 后端服务设置环境变量：
   - `DATABASE_URL`：改为 Railway MySQL 的连接串（`mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4`，可从 Railway MySQL 变量拼接）
   - `JWT_SECRET_KEY`：Railway 生成随机值
   - `ADMIN_PASSWORD`：自定义
   - `CORS_ORIGINS`：你的前端域名
5. 前端服务 `VITE_API_BASE_URL` 指向后端域名
6. Railway 会自动构建 Dockerfile 并分配 `*.up.railway.app` 永久域名（免费额度足够小项目）

### 方案 B：VPS + Docker Compose（完全可控）

任选一台 Linux 服务器（阿里云 / 腾讯云 / 任意 VPS，1C2G 即可）：

```bash
# 在服务器上
git clone https://github.com/你的用户名/lost-and-found-agent.git
cd lost-and-found-agent

# 修改生产密钥
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export ADMIN_PASSWORD="你的管理员密码"
export MYSQL_PASSWORD="你的数据库密码"

docker compose -f docker/docker-compose.yml up -d --build
```

访问 `http://服务器IP:8080`（前端）；建议再配 Nginx + HTTPS（见 `docs/deployment.md`）。

### 方案 C：Render 后端 + Vercel/Netlify 前端 + 云端 MySQL

1. **MySQL**：用 PlanetScale（免费额度，MySQL 兼容）或 Railway MySQL，拿到连接串
2. **后端**：Render（https://render.com）New Web Service → 连 GitHub 仓库 → Dockerfile 路径 `backend/Dockerfile` → 环境变量填 `DATABASE_URL` / `JWT_SECRET_KEY` / `ADMIN_PASSWORD` / `CORS_ORIGINS` → Health Check Path 填 `/health`
3. **前端**：Vercel 或 Netlify 导入仓库，构建命令 `pnpm install && pnpm run build`，输出目录 `frontend/dist`，环境变量 `VITE_API_BASE_URL` 指向 Render 后端域名
4. Render/Vercel 都会提供永久域名

## 三、可选：开启图片识别的大模型能力

图片识别默认用本地 Pillow 检测主色/亮度（无需任何配置）。要启用**视觉大模型**识别类别/颜色/品牌/描述：

1. 到 DeepSeek（https://platform.deepseek.com）等平台申请 API Key
2. 后端环境变量设置：

```text
LLM_API_KEY=你的密钥
LLM_BASE_URL=https://api.deepseek.com   # 或其它 OpenAI 兼容地址
LLM_MODEL=deepseek-chat                 # 或支持视觉的模型
```

不配置也能正常使用，Agent 自动回退到本地规则引擎。

## 四、上线后检查清单

- [ ] `GET /health` 返回 `{"status":"ok","database":"connected"}`
- [ ] 注册 / 登录正常，管理员账号能进后台
- [ ] 发布物品 → 审核 → 公开可见 → 智能匹配有结果
- [ ] 图片上传后颜色识别正常
- [ ] CI 徽章为绿色（GitHub Actions 全部通过）
