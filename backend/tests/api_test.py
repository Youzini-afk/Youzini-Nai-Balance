import base64
import os

from fastapi.testclient import TestClient


def _set_env():
    key = base64.urlsafe_b64encode(b"1" * 32).decode("ascii")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("ENCRYPTION_KEY", key)
    os.environ["DATABASE_URL"] = (
        "sqlite+aiosqlite:///file:novelai_api_memdb?mode=memory&cache=shared&uri=true"
    )
    os.environ.setdefault("ALLOW_REGISTRATION", "true")
    os.environ.setdefault("AUTO_QUOTA_ENABLED", "true")
    os.environ.setdefault("BASE_RPM", "1")
    os.environ.setdefault("PER_KEY_RPM", "0")
    os.environ.setdefault("MAX_RPM", "1")
    os.environ.setdefault("ADMIN_USERNAME", "admin")
    os.environ.setdefault("ADMIN_PASSWORD", "admin123")


def _login(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def run():
    _set_env()
    from app.main import app

    with TestClient(app) as client:
        resp = client.post(
            "/auth/register",
            json={"username": "user1", "password": "pass1234", "email": "u1@example.com"},
        )
        assert resp.status_code in (200, 409), resp.text

        user_token = _login(client, "user1", "pass1234")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Non-admin should be forbidden
        resp = client.get("/admin/users", headers=user_headers)
        assert resp.status_code == 403, resp.text

        # Admin access
        admin_token = _login(client, "admin", "admin123")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        resp = client.get("/admin/users", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        users = resp.json()
        user_row = next(u for u in users if u["username"] == "user1")

        # Update manual RPM
        resp = client.patch(
            f"/admin/users/{user_row['id']}",
            headers=admin_headers,
            json={"manual_rpm": 5},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["manual_rpm"] == 5

        # Disable user
        resp = client.patch(
            f"/admin/users/{user_row['id']}",
            headers=admin_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_active"] is False

        # Ensure disabled user cannot access
        resp = client.get("/auth/me", headers=user_headers)
        assert resp.status_code == 403, resp.text

        # Re-enable user
        resp = client.patch(
            f"/admin/users/{user_row['id']}",
            headers=admin_headers,
            json={"is_active": True, "manual_rpm": None},
        )
        assert resp.status_code == 200, resp.text

        # Rate limit: force zero RPM and expect 429
        resp = client.patch(
            f"/admin/users/{user_row['id']}",
            headers=admin_headers,
            json={"manual_rpm": 0},
        )
        assert resp.status_code == 200, resp.text

        resp = client.post("/v1/novelai/generate-image", headers=user_headers, json={})
        assert resp.status_code == 429, resp.text

        # Admin config read/update
        resp = client.get("/admin/config", headers=admin_headers)
        assert resp.status_code == 200, resp.text

        resp = client.post(
            "/admin/config",
            headers=admin_headers,
            json={"key": "base_rpm", "value": "2"},
        )
        assert resp.status_code == 200, resp.text

        # Generate a client API key and call models with it (no JWT)
        resp = client.post("/client-keys", headers=user_headers, json={"name": "cli", "rotate": True})
        assert resp.status_code == 200, resp.text
        api_key = resp.json()["api_key"]
        resp = client.get("/v1/novelai/models", headers={"Authorization": f"Bearer {api_key}"})
        assert resp.status_code == 200, resp.text

        # Disable then re-enable client key
        keys = client.get("/client-keys", headers=user_headers).json()
        key_id = keys[0]["id"]
        resp = client.patch(
            f"/client-keys/{key_id}",
            headers=user_headers,
            json={"is_active": False},
        )
        assert resp.status_code == 200, resp.text
        resp = client.get("/v1/novelai/models", headers={"Authorization": f"Bearer {api_key}"})
        assert resp.status_code == 401, resp.text

        resp = client.patch(
            f"/client-keys/{key_id}",
            headers=user_headers,
            json={"is_active": True},
        )
        assert resp.status_code == 200, resp.text
        resp = client.get("/v1/novelai/models", headers={"Authorization": f"Bearer {api_key}"})
        assert resp.status_code == 200, resp.text

        # Delete client key
        resp = client.delete(f"/client-keys/{key_id}", headers=user_headers)
        assert resp.status_code == 200, resp.text
        resp = client.get("/client-keys", headers=user_headers)
        assert resp.status_code == 200, resp.text
        assert len(resp.json()) == 0
        resp = client.get("/v1/novelai/models", headers={"Authorization": f"Bearer {api_key}"})
        assert resp.status_code == 401, resp.text

    print("API test passed.")


if __name__ == "__main__":
    run()
