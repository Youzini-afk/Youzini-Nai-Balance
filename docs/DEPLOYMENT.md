<!--
PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD_PAD
-->
# 部署指南（中文）

本项目包含：
- `backend/`：FastAPI 服务（同时托管静态前端）
- `frontend/`：纯静态前端（由后端 `/` + `/assets` 提供）

## 1. 单机部署（Ubuntu 24 / 常规 VPS）

### 1.1 安装依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 1.2 上传代码并创建虚拟环境

假设代码位于 `/www/wwwroot/youzini-nai-pool`：

```bash
cd /www/wwwroot/youzini-nai-pool/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.3 配置 `.env`

复制模板：

```bash
cp .env.example .env
```

生成 `ENCRYPTION_KEY`（URL-safe base64，32 字节）：

```bash
source .venv/bin/activate
python - << 'PY'
from app.services.crypto import generate_key
print(generate_key())
PY
```

然后将输出填入 `.env` 的 `ENCRYPTION_KEY`，同时设置：
- `SECRET_KEY`（JWT 密钥）
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`

### 1.4 启动服务

```bash
source .venv/bin/activate
python run.py
```

默认监听 `0.0.0.0:5002`：
- Web UI：`http://服务器IP:5002/`
- 探活：`GET /healthz`、`GET /readyz`

## 2. Nginx 反向代理（推荐）

示例（80 端口反代到 5002）：

```nginx
server {
  listen 80;
  server_name example.com;

  location / {
    proxy_pass http://127.0.0.1:5002;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
  }
}
```

如果你启用“使用日志记录 IP”，并且服务在 Nginx 之后，请在 `.env` 设置：

```
TRUST_PROXY_HEADERS=true
```

## 3. 宝塔（BT-Panel）注意事项

宝塔可能对环境变量输入有格式限制，推荐：
- 在 `backend/` 目录使用 `.env` 文件（本项目默认读取 `.env`）
- 使用虚拟环境安装依赖（Ubuntu 24 默认启用 PEP 668，系统 Python 会拒绝全局 pip）

典型启动命令（宝塔 Python 项目“命令行启动”）：

```bash
cd /www/wwwroot/youzini-nai-pool/backend && \
source .venv/bin/activate && \
python run.py
```

## 4. 多机高可用（共享数据库）

### 4.1 关键原则

多机共享同一数据（用户/池/日志）时：
- 必须使用 Postgres（SQLite 不适合多机共享）
- 所有节点必须使用相同的：
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `ENCRYPTION_KEY`
- 开启多机行为：`MULTI_NODE_ENABLED=true`（默认 false）

### 4.2 Docker Compose 演示

项目提供一个演示配置：
- `deploy/docker-compose.multi_node.yml`
- `deploy/nginx.docker.multi_node.conf`

在项目根目录：

```bash
docker compose -f deploy/docker-compose.multi_node.yml up -d --build
```

访问：`http://127.0.0.1:8080`（Nginx → 两个后端节点）

### 4.3 Leader-only（推荐）

共享 DB 时，“健康检测 / 代理探活”等循环任务不应在每个节点都跑。

建议指定一个 Leader 节点：

```
HEALTH_CHECK_LEADER_ONLY=true
HEALTH_CHECK_LEADER_NODE_ID=node-1
UPSTREAM_PROXY_KEEPALIVE_LEADER_ONLY=true
UPSTREAM_PROXY_KEEPALIVE_LEADER_NODE_ID=node-1
```

也可在管理后台页面配置（写入 DB，节点会自动同步）。

