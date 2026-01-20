<!--
PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD
-->
# 配置说明（中文）

本项目读取 `.env`（Pydantic Settings，大小写不敏感）。

模板参考：
- `.env.example`
- `backend/.env.example`

## 1) 必填/强烈建议配置

- `SECRET_KEY`：JWT 签名密钥（多机必须一致）
- `ENCRYPTION_KEY`：AES-256-GCM 密钥（多机必须一致）
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `DATABASE_URL`：单机可用 SQLite；多机共享必须 Postgres

## 2) 单机 / 多机

- `MULTI_NODE_ENABLED`：多机行为总开关（默认 `false`）
  - 关闭：不会从 DB 同步 SystemConfig，也不会启用 Leader-only 逻辑
  - 开启：会从共享 DB 同步允许的 SystemConfig 配置（见下）

## 3) 后台任务（健康检测 / 探活）

- `HEALTH_CHECK_ENABLED`：是否启用 Key 健康检测循环
- `HEALTH_CHECK_INTERVAL_SECONDS`：检测间隔
- `HEALTH_CHECK_LEADER_ONLY` / `HEALTH_CHECK_LEADER_NODE_ID`：多机时只允许 leader 跑检测（推荐）

## 4) 安全相关

- `CORS_ALLOW_ORIGINS`：默认空（禁用 CORS）；需要时填逗号分隔列表或 `*`
- `CORS_ALLOW_CREDENTIALS`：默认 false
- `TRUST_PROXY_HEADERS`：默认 false；仅在反代后启用，用于信任 `X-Real-IP/X-Forwarded-For`

## 5) 登录/注册防爆破

- `AUTH_LOGIN_RATE_LIMIT_PER_MINUTE`：同 IP 登录频率限制（默认 20）
- `AUTH_REGISTER_RATE_LIMIT_PER_MINUTE`：同 IP 注册频率限制（默认 10）
- `AUTH_LOGIN_LOCKOUT_THRESHOLD` / `AUTH_LOGIN_LOCKOUT_MINUTES`：失败次数锁定（默认 10 次/10 分钟）
- `AUTH_PASSWORD_MIN_LENGTH`：最小密码长度（默认 8）

## 6) 哪些配置可以在网页里改？

管理员页面使用 `/admin/config` 写入 `SystemConfig`。为安全起见，下列配置禁止通过该接口修改：

- 密钥与身份相关：`secret_key`, `encryption_key`, `admin_password`, `admin_username`
- 部署关键：`database_url`, `node_id`, `multi_node_enabled`
- 启动期安全参数：`cors_allow_origins`, `cors_allow_credentials`, `trust_proxy_headers`

其余大部分“业务参数”（RPM、冷却、代理池、探活等）可在网页里修改并同步到节点。

