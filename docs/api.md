# API 文档

交互式文档（Swagger UI）：启动后端后访问 `http://127.0.0.1:8000/docs`。

## 通用约定

- 业务接口前缀 `/api`；健康检查在根路径 `/health`
- 认证方式：请求头 `Authorization: Bearer <JWT>`
- 错误响应统一为 `{"detail": "中文说明"}`，状态码语义：400 参数/业务错误、401 未登录或凭证无效、403 无权限或账号禁用、404 不存在、409 冲突、422 参数校验失败
- 分页参数：`page`（从 1 开始）、`size`；返回 `{items, total, page, size}`

## 认证与用户

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 注册（成功即自动登录） | 公开 |
| POST | `/api/auth/login` | 登录（用户名 / 邮箱 / 手机号） | 公开 |
| GET | `/api/users/me` | 当前用户资料 | 登录 |
| PUT | `/api/users/me` | 修改资料 | 登录 |
| PUT | `/api/users/me/password` | 修改密码 | 登录 |

## 物品

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/items` | 发布失物 / 招领（进入待审核） | 登录 |
| GET | `/api/items` | 列表搜索（q/item_type/category/location/sort/page/size/mine） | 公开 |
| GET | `/api/items/categories` | 物品分类 | 公开 |
| GET | `/api/items/{id}` | 详情（待审核仅本人 / 管理员可见） | 公开 |
| PUT | `/api/items/{id}` | 编辑（重新进入审核） | 本人 / 管理员 |
| DELETE | `/api/items/{id}` | 删除 | 本人 / 管理员 |
| POST | `/api/items/{id}/images` | 上传图片（multipart，字段名 files） | 本人 / 管理员 |
| DELETE | `/api/items/{id}/images/{index}` | 删除第 index 张图片 | 本人 / 管理员 |

## 认领

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/items/{id}/claims` | 提交认领申请（multipart：proof_description/contact/files） | 登录 |
| GET | `/api/claims/my` | 我的认领申请 | 登录 |
| GET | `/api/claims/received` | 收到我物品的认领申请 | 登录 |
| POST | `/api/claims/{id}/images` | 补充证明图片（回到待处理） | 申请人 |
| PUT | `/api/claims/{id}/approve` | 同意（物品标记已认领，其余申请自动拒绝） | 物品发布者 |
| PUT | `/api/claims/{id}/reject` | 拒绝 | 物品发布者 |
| PUT | `/api/claims/{id}/request-proof` | 要求补充证明 | 物品发布者 |
| DELETE | `/api/claims/{id}` | 撤回申请 | 申请人 |

## 智能匹配

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/matches/analyze` | `{"item_id": n}` 运行 Agent 分析 | 本人 / 管理员 |
| GET | `/api/matches/recommendations?item_id=n` | 查看匹配推荐（无记录时现场计算） | 公开（物品可见即可） |
| GET | `/api/matches/{id}` | 匹配详情 | 公开（物品可见即可） |

## 消息

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| GET | `/api/messages?box=inbox|sent` | 消息列表 | 登录 |
| GET | `/api/messages/unread-count` | 未读数 | 登录 |
| PUT | `/api/messages/{id}/read` | 标记已读 | 收件人 |
| PUT | `/api/messages/read-all` | 全部已读 | 登录 |
| POST | `/api/messages/send` | 发送私信 `{receiver_id, content}` | 登录 |

## 举报与公告

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | `/api/reports` | 提交举报（target_type: item/user/claim） | 登录 |
| GET | `/api/reports/my` | 我的举报 | 登录 |
| GET | `/api/announcements` | 生效中的公告 | 公开 |

## 管理端（全部需要管理员）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/statistics` | 数据统计 |
| GET | `/api/admin/items/pending` | 待审核物品 |
| PUT | `/api/admin/items/{id}/audit` | `{decision: approve|reject, comment}` |
| DELETE | `/api/admin/items/{id}` | 删除违规物品 |
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/{id}/status` | `{status: active|disabled}` |
| GET | `/api/admin/claims` | 全部认领申请 |
| GET | `/api/admin/reports` | 举报列表 |
| PUT | `/api/admin/reports/{id}/handle` | `{action: handled|dismissed, comment}` |
| GET/POST | `/api/admin/announcements` | 公告列表 / 发布 |
| PUT/DELETE | `/api/admin/announcements/{id}` | 公告编辑 / 删除 |
| GET | `/api/admin/agent-logs` | Agent 运行日志 |
| GET | `/api/admin/operation-logs` | 操作审计日志 |
