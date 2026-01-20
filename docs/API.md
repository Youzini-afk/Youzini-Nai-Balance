<!--
PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD
-->
# API 说明（中文）

Base URL（示例）：

```
http(s)://你的域名或IP:5002/v1/novelai
```

## 认证方式

### 1) JWT（网页登录）

- `POST /auth/login` 获取 `access_token`
- 请求头：`Authorization: Bearer <jwt>`

### 2) 中转 API Key（推荐给脚本/客户端）

- 登录后在网页生成 “中转 API Key（np-xxxx）”
- 请求头：`Authorization: Bearer np-xxxx`

## 主要接口

### 认证

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### NovelAI 中转

- `GET /v1/novelai/models`：获取可用绘图模型列表
- `POST /v1/novelai/generate-image`：转发到 `https://image.novelai.net/ai/generate-image`

### Key 池管理（管理员）

- `POST /admin/keys`：上传 NovelAI Key 到池（加密存储；支持多行/逗号分隔）

### 中转 Key 管理（用户）

- `POST /client-keys`：生成中转 API Key（可选 rotate）
- `GET /client-keys`：我的中转 Key 列表
- `PATCH /client-keys/{id}`：启用/禁用
- `DELETE /client-keys/{id}`：删除

### 管理员

- `GET /admin/users`
- `PATCH /admin/users/{id}`：设置 `manual_rpm` 或 `is_active`
- `GET /admin/keys`
- `POST /admin/keys`
- `POST /admin/keys/{id}/toggle`
- `GET /admin/config` / `POST /admin/config`
- `POST /admin/health-check`
- `GET /admin/logs`
- `GET /admin/proxy-pool`

## Curl 示例

1) 登录（JWT）：

```bash
curl -s http://127.0.0.1:5002/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"change-me"}'
```

2) 使用中转 Key 调用模型列表：

```bash
curl -s http://127.0.0.1:5002/v1/novelai/models \
  -H 'Authorization: Bearer np-xxxx'
```

