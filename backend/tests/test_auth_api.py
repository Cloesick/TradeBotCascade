"""
End-to-end auth flow through the FastAPI app (register -> login -> me ->
refresh). Exercises the bcrypt hashing path and JWT signing/verification over
real HTTP via Starlette's TestClient (no network).
"""
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_default_admin_login(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_wrong_password_rejected(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_register_login_me_refresh_flow(client):
    creds = {
        "username": "tester_e2e",
        "email": "tester_e2e@example.com",
        "password": "Sup3rSecret",
        "full_name": "E2E Tester",
    }
    # register
    r = client.post("/auth/register", json=creds)
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "tester_e2e"

    # login
    r = client.post("/auth/login", json={"username": creds["username"], "password": creds["password"]})
    assert r.status_code == 200, r.text
    tokens = r.json()

    # authenticated /auth/me
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200, r.text
    assert r.json()["username"] == "tester_e2e"

    # refresh issues a fresh, valid access token
    r = client.post("/auth/refresh", params={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text
    new_access = r.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r.status_code == 200


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code in (401, 403)
