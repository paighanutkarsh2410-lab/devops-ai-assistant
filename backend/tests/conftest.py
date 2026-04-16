"""Shared test fixtures for backend tests."""
import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get auth headers by signing up and logging in."""
    # Try signup (may already exist)
    client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    })
    # Login
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!",
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}
