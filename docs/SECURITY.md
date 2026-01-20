<!--
PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD
-->
# 安全与运维建议（中文）

## 1) 密钥与机密

- 不要把 `.env`、数据库文件、备份中包含的敏感信息提交到公开仓库
- `SECRET_KEY`、`ENCRYPTION_KEY`、`ADMIN_PASSWORD` 必须使用高强度随机值
- 多机共享 DB 时所有节点必须使用相同的 `SECRET_KEY`/`ENCRYPTION_KEY`

## 2) TLS

强烈建议在 Nginx/宝塔层启用 HTTPS。

## 3) CORS

默认 `CORS_ALLOW_ORIGINS=`（禁用 CORS）。只有在你明确需要跨域访问时才开启，并收敛到具体域名列表。

## 4) 反代与真实 IP

本项目不再记录/展示请求 IP。

若站点在 Nginx 等反代之后，为了让登录/注册防爆破更准确，请设置 `TRUST_PROXY_HEADERS=true`，
并由反代写入 `X-Real-IP/X-Forwarded-For`。

## 5) 防爆破与滥用

- 登录/注册启用了基础防爆破（IP 频率限制、失败锁定）
- 建议配合 WAF/Fail2ban（可选）进一步加固

## 6) 代理池

代理池仅用于线路容灾/保活，不用于规避限制。
