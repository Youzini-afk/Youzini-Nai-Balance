# Contributing Guide (English)

## 1) Dev environment

- Python: recommended `3.12+`
- Windows: PowerShell + venv works as well

Install backend deps:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Run

Create `backend/.env` from `backend/.env.example`, fill `SECRET_KEY`, `ENCRYPTION_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.

```bash
python run.py
```

Open `http://127.0.0.1:5002/`.

## 3) Tests

```bash
$env:PYTHONPATH='.'
python tests/smoke_test.py
python tests/api_test.py
```

## 4) Conventions

The current codebase leans towards “minimal, readable, operable” style. This is informational (not strict rules):

- Python: FastAPI + SQLAlchemy Async, prefer clear naming over short names
- Config: centralized in `backend/app/config.py`; secrets are `.env` only
- Security defaults: CORS off by default, do not trust proxy IP headers by default, avoid unescaped `innerHTML` in frontend
- Layout: routes in `backend/app/routers/`, core logic in `backend/app/services/`, background loops in `backend/app/tasks/`

## 5) PR checklist

- Security impact reviewed (auth, XSS, CORS, logs, sensitive config)
- Docs updated if needed (`README.md` / `docs/`)
- Tests updated or manual steps recorded
- Multi-node: avoid duplicated background tasks (leader-only)
