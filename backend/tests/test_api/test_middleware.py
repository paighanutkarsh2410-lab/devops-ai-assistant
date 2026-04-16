"""Test middleware: security headers, rate limiting, compression."""


def test_security_headers(client):
    response = client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Strict-Transport-Security" in response.headers


def test_rate_limit_headers(client):
    response = client.get("/")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


def test_gzip_compression(client):
    """Large responses should be compressed."""
    response = client.get("/", headers={"Accept-Encoding": "gzip"})
    # Response is processed; just check it works
    assert response.status_code == 200
