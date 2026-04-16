"""Test authentication endpoints."""
import uuid


def test_signup_success(client):
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/auth/signup", json={
        "email": email,
        "password": "SecurePass1!",
        "full_name": "Test User",
    })
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["email"] == email


def test_signup_duplicate(client):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"email": email, "password": "SecurePass1!"})
    response = client.post("/auth/signup", json={"email": email, "password": "SecurePass1!"})
    assert response.status_code == 400


def test_login_success(client):
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"email": email, "password": "SecurePass1!"})
    response = client.post("/auth/login", json={"email": email, "password": "SecurePass1!"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    email = f"wrong-{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/signup", json={"email": email, "password": "SecurePass1!"})
    response = client.post("/auth/login", json={"email": email, "password": "WrongPass1!"})
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    if not auth_headers:
        return
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()


def test_protected_endpoint_no_token(client):
    response = client.get("/incidents/")
    assert response.status_code in (401, 403)
