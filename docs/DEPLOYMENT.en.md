# Deployment Guide (English)

This repo contains:
- `backend/`: FastAPI service (also serves the static frontend)
- `frontend/`: static frontend (served by backend `/` and `/assets`)

## 1. Single-node deployment (Ubuntu 24 / VPS)

### 1.1 Install dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 1.2 Create virtualenv

```bash
cd /www/wwwroot/youzini-nai-pool/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.3 Configure `.env`

```bash
cp .env.example .env
```

Generate `ENCRYPTION_KEY`:

```bash
python - << 'PY'
from app.services.crypto import generate_key
print(generate_key())
PY
```

Fill `.env`: `ENCRYPTION_KEY`, `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.

### 1.4 Run

```bash
python run.py
```

Default: `0.0.0.0:5002`
- Web UI: `http://server-ip:5002/`
- `GET /healthz`, `GET /readyz`

## 2. Nginx reverse proxy

If you enable IP logging behind Nginx, set:

```
TRUST_PROXY_HEADERS=true
```

## 3. Multi-node (shared DB)

### 3.1 Rules

- Use Postgres (SQLite is not suitable)
- All nodes must share the same `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`
- Enable multi-node behaviors: `MULTI_NODE_ENABLED=true` (default off)

### 3.2 Docker compose demo

```bash
docker compose -f deploy/docker-compose.multi_node.yml up -d --build
```

Visit: `http://127.0.0.1:8080`

### 3.3 Leader-only loops (recommended)

Enable leader-only to avoid duplicated background traffic:

```
HEALTH_CHECK_LEADER_ONLY=true
HEALTH_CHECK_LEADER_NODE_ID=node-1
UPSTREAM_PROXY_KEEPALIVE_LEADER_ONLY=true
UPSTREAM_PROXY_KEEPALIVE_LEADER_NODE_ID=node-1
```


