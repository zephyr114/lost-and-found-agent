# 单镜像部署 Dockerfile（Hugging Face Spaces 免费 Docker 运行）
# 构建上下文必须是仓库根目录：docker build -f deploy/hf/Dockerfile .

# ---- 阶段 1：构建前端 ----
FROM node:22-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend ./
RUN pnpm run build

# ---- 阶段 2：后端 + 前端产物 ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY --from=frontend /fe/dist ./frontend_dist
RUN mkdir -p uploads
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
