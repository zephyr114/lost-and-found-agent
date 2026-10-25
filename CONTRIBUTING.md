# 贡献指南

感谢你对失物招领智能平台的关注！欢迎提交 Issue 和 Pull Request。

## 快速上手

```bash
# 后端
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload

# 前端
cd frontend
pnpm install && pnpm dev
```

## 提交前检查

- 后端：`cd backend && .venv\Scripts\python -m pytest`（全部用例通过）
- 前端：`cd frontend && pnpm run build`（类型检查 + 构建通过）

## 代码规范

- 后端遵循分层：`api`（路由）→ `services`（业务）→ `models`（数据），敏感配置一律走环境变量
- 前端使用 TypeScript，路由按权限配置 `meta.requiresAuth / requiresAdmin`
- 提交信息用中文，格式：`类型：简述`（如 `feat：新增图片识别`）

## 分支约定

- `main` 为稳定分支
- 新功能 / 修复请从 `main` 新建分支，完成后提交 PR
