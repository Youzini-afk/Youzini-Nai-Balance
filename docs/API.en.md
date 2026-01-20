# API (English)

Base URL (example):

```
http(s)://your-domain-or-ip:5002/v1/novelai
```

## Auth

### JWT (web login)

- `POST /auth/login` to obtain `access_token`
- Header: `Authorization: Bearer <jwt>`

### Client API key (recommended for scripts)

- Generate `np-xxxx` in the web UI
- Header: `Authorization: Bearer np-xxxx`

## Key endpoints (high level)

- `GET /v1/novelai/models`
- `POST /v1/novelai/generate-image`
- `POST /client-keys`, `GET /client-keys`, `PATCH /client-keys/{id}`, `DELETE /client-keys/{id}`
- Admin: `POST /admin/keys`, `GET /admin/users`, `GET /admin/keys`, `POST /admin/config`, `GET /admin/logs`, ...

## Curl

```bash
curl -s http://127.0.0.1:5002/v1/novelai/models \
  -H 'Authorization: Bearer np-xxxx'
```

