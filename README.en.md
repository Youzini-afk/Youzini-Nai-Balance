# Nai-Balance (Relay / Key Pool)

A lightweight NovelAI relay service: admins maintain a NovelAI key pool; the platform computes rate limits based on healthy keys in the pool and config, and provides health checks, load balancing, cooldown/backoff, and audit logs for upstream requests.

## Features

- Accounts: register/login, JWT auth
- Client keys: generate `np-xxxx` keys for scripts/clients (never exposes users’ NovelAI keys)
- Key pool: admin-managed NovelAI keys (AES-256-GCM at rest), dedup, periodic health checks, failure cooldown, round-robin selection
- Rate limiting: pool-size-based RPM (auto/manual modes)
- Upstream proxy pool (optional): availability/failover only (not for bypassing restrictions)
- Usage logs: users see their own; admins can view global logs
- Multi-node HA: Nginx load balancing + Postgres shared DB + node identity header + leader-only background tasks

## Quick start (single node)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Create `.env` from `.env.example` and set `ENCRYPTION_KEY`:

```bash
python - << 'PY'
from app.services.crypto import generate_key
print(generate_key())
PY
```

Open:
- Web UI: `http://127.0.0.1:5002/`
- `GET /healthz`
- `GET /readyz`

## API Base URL

```
http(s)://your-domain-or-ip:5002/v1/novelai
```

For scripts/clients, use the generated client API key:

```
Authorization: Bearer np-xxxx
```

See `docs/API.en.md` for endpoints and examples.

## Multi-node (shared database)

Multi-node behaviors are guarded by `MULTI_NODE_ENABLED=true` (default off).

**Important**
- All nodes must share the same `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`
- Use Postgres for shared state (SQLite is not suitable)
- Response header `X-NovelAIPool-Node` shows which node served the request

Examples:
- Nginx sample: `deploy/nginx.multi_node.conf`
- Docker compose demo: `deploy/docker-compose.multi_node.yml` (exposes `http://127.0.0.1:8080`)

Full guide: `docs/DEPLOYMENT.en.md`.

## Security

- CORS is disabled by default (`CORS_ALLOW_ORIGINS=`). Enable only if you need cross-origin access.
- If you are behind Nginx, set `TRUST_PROXY_HEADERS=true` so login/register anti-bruteforce uses `X-Real-IP` / `X-Forwarded-For`.
- Basic anti-bruteforce protections are enabled for login/register (see `AUTH_LOGIN_*` / `AUTH_REGISTER_*`).

See `docs/SECURITY.en.md`.

## Maintainer note (avoid committing sensitive files)

- Do not commit: `backend/.env`, `.env`, `backend/data/*.db*`, `*.sqlite*`, `*.log`, or reverse-proxy configs with real domains/cert paths.
- The runtime SQLite database defaults to `backend/data/novelai_pool.db` and may contain users/keys/usage logs.
- Before you commit/push, check `git status` to avoid uploading runtime files.

## License

PolyForm Noncommercial License 1.0.0. See `LICENSE`.



