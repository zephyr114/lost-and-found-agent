# Hugging Face Spaces 部署说明

本目录用于把项目以「单镜像」方式部署到 Hugging Face Spaces 免费 Docker 环境。

## 结构

- `Dockerfile`：多阶段构建（Node 构建前端 → Python 运行后端并托管前端）
- 部署时会把仓库整体推送到 HF Space 仓库，并在根目录生成：
  - `Dockerfile`（本文件内容的拷贝）
  - `README.md`（带 HF Space 元数据头）

## 需要的环境变量（在 Space 的 Settings → Variables and secrets 中配置）

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | Neon 免费 PostgreSQL 连接串（`postgresql://...`） |
| `JWT_SECRET_KEY` | 随机长字符串 |
| `ADMIN_PASSWORD` | 管理员初始密码 |
| `CORS_ORIGINS` | 填 `*` |
| `PORT` | `7860`（HF Spaces 固定端口） |

## 自定义域名

HF Spaces 免费版不直接支持绑定域名，但可以用 **Cloudflare 免费版** 做反向代理：
在 Cloudflare 域名 DNS 里添加 CNAME（开启代理）指向 `https://<你的空间>.hf.space` 即可。
