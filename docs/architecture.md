# 架构文档

## 1. 系统架构

```text
用户端 Vue 3 (SPA)
        ↓
Nginx（静态资源 + 反向代理）
        ↓
FastAPI 后端服务
        ↓
业务服务层
├── 用户服务 user_service
├── 物品服务 item_service
├── 认领服务 claim_service
├── 消息服务 message_service
├── 管理服务 admin_service
└── Agent 服务 agents/matching
        ↓
数据层
├── MySQL（生产） / SQLite（开发）
├── Redis（预留）
├── 本地 uploads（开发） / MinIO（预留）
└── 向量检索（预留 FAISS / Chroma）
        ↓
AI 能力层（可选，未配置则走规则引擎）
├── 大语言模型（DeepSeek 等 OpenAI 兼容接口）
```

## 2. 技术栈

- 前端：Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router + Axios + ECharts
- 后端：Python 3.12 + FastAPI + SQLAlchemy 2 + Pydantic v2 + PyJWT + bcrypt
- 数据：MySQL 8（生产）/ SQLite（开发）、Redis、MinIO（预留）
- 部署：Docker + Docker Compose + Nginx

## 3. 后端分层

| 层 | 目录 | 职责 |
| --- | --- | --- |
| 路由 | `app/api/` | HTTP 接口、参数校验、权限依赖 |
| 业务服务 | `app/services/` | 业务规则、事务、状态流转、通知 |
| 数据访问 | `app/models/` + SQLAlchemy Session | ORM 模型与会话 |
| 模式 | `app/schemas/` | Pydantic 请求 / 响应模型 |
| 配置 | `app/core/` | 环境变量配置、密码哈希、JWT |
| Agent | `app/agents/` | 智能匹配流水线与工具 |
| 工具 | `app/utils/` | 地理距离、文件上传 |

## 4. 关键设计

### 4.1 审核流

发布 → `audit_status=pending`（仅本人 / 管理员可见）→ 管理员通过 / 拒绝 → 通过后公开可见并触发智能匹配 → 修改内容后重新进入待审核。

### 4.2 认领状态机

```text
pending ──同意──▶ approved（物品 status=claimed，其余申请自动 rejected）
   │──拒绝──▶ rejected
   │──要求补充证明──▶ need_more_proof ──补充材料──▶ pending
   └──申请人撤回──▶ cancelled
```

### 4.3 智能匹配 Agent

工具链：`extract_item_attributes` → `search_similar_items` → `calculate_match_score` → `create_match_notification` → `submit_audit_task` → 全程写入 `agent_logs`。

打分权重：类别 30、名称相似度 15、颜色 10、品牌 10、时间差 15、地点距离 15、描述特征重合 15（总分 100，阈值 40 生成匹配记录）。

属性提取默认使用内置规则引擎（零外部依赖）；配置 `LLM_API_KEY` 后自动切换为 DeepSeek 等 OpenAI 兼容接口。

### 4.4 安全

- 密码 bcrypt 哈希；JWT HS256（密钥来自环境变量，绝不入库入代码）
- 三层依赖：`get_current_user_optional`（公开 + 可选登录）→ `get_current_user`（登录）→ `get_current_admin`（管理员）
- 前端路由守卫 `requiresAuth` / `requiresAdmin` / `guestOnly`；Axios 401 统一登出跳转
- 图片上传类型 / 大小双重校验；上传文件目录 git 忽略
- 敏感配置全部走 `.env`（`.env.example` 为模板）

## 5. 目录结构

见项目根目录 README.md「目录结构」章节。
