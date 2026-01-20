import base64
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient


def _set_env():
    key = base64.urlsafe_b64encode(b"0" * 32).decode("ascii")
    db_url = "sqlite+aiosqlite:///file:novelai_memdb?mode=memory&cache=shared&uri=true"
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("ENCRYPTION_KEY", key)
    os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("ALLOW_REGISTRATION", "true")
    os.environ.setdefault("AUTO_QUOTA_ENABLED", "true")
    os.environ.setdefault("BASE_RPM", "5")
    os.environ.setdefault("PER_KEY_RPM", "10")
    os.environ.setdefault("MAX_RPM", "30")
    os.environ.setdefault("ADMIN_USERNAME", "admin")
    os.environ.setdefault("ADMIN_PASSWORD", "admin123")


def run():
    _set_env()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.main import app

    with TestClient(app) as client:
        r = client.post(
            "/auth/register",
            json={"username": "tester", "password": "pass1234", "email": "t@example.com"},
        )
        assert r.status_code in (200, 409), r.text

        r = client.post("/auth/login", json={"username": "tester", "password": "pass1234"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}

        r = client.get("/auth/me", headers=headers)
        assert r.status_code == 200, r.text

        r = client.post(
            "/auth/login",
            json={
                "username": os.environ["ADMIN_USERNAME"],
                "password": os.environ["ADMIN_PASSWORD"],
            },
        )
        assert r.status_code == 200, r.text
        admin_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = client.post(
            "/admin/keys",
            headers=admin_headers,
            json={"api_keys": "fake-key-for-test", "verify_now": False},
        )
        assert r.status_code == 200, r.text

        r = client.post(
            "/v1/novelai/generate-image",
            headers=headers,
            json={},
        )
        assert r.status_code in (400, 503), r.text

        r = client.get("/logs", headers=headers)
        assert r.status_code == 200, r.text
        assert len(r.json()) >= 1

    print("Smoke test passed.")


if __name__ == "__main__":
    run()
