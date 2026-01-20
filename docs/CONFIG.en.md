# Configuration (English)

The service reads `.env` (Pydantic Settings, case-insensitive).

Templates:
- `.env.example`
- `backend/.env.example`

## Required / recommended

- `SECRET_KEY`: JWT signing key (must be the same across nodes)
- `ENCRYPTION_KEY`: AES-256-GCM key (must be the same across nodes)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `DATABASE_URL`: SQLite for single node; Postgres for multi-node shared DB

## Multi-node switch

- `MULTI_NODE_ENABLED`: master switch (default `false`)
  - Off: no DB-driven SystemConfig refresh; leader-only logic is ignored
  - On: nodes refresh allowed SystemConfig keys from DB

## Security

- `CORS_ALLOW_ORIGINS`: default empty (CORS disabled); set comma-separated origins or `*` if needed
- `CORS_ALLOW_CREDENTIALS`: default false
- `TRUST_PROXY_HEADERS`: default false; set true only behind a trusted reverse proxy

## Anti-bruteforce

- `AUTH_LOGIN_RATE_LIMIT_PER_MINUTE`
- `AUTH_REGISTER_RATE_LIMIT_PER_MINUTE`
- `AUTH_LOGIN_LOCKOUT_THRESHOLD` / `AUTH_LOGIN_LOCKOUT_MINUTES`
- `AUTH_PASSWORD_MIN_LENGTH`

## Which configs are editable via the admin UI?

`/admin/config` writes `SystemConfig`. Sensitive keys are blocked (secrets, DB URL, multi-node switch, CORS/proxy trust knobs).


