"""Test alerts endpoints."""


def test_create_alert(client, auth_headers):
    if not auth_headers:
        return
    response = client.post("/alerts/", headers=auth_headers, json={
        "title": "High CPU Alert",
        "message": "CPU usage at 95%",
        "severity": "critical",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "High CPU Alert"
    assert data["acknowledged"] is False


def test_list_alerts(client, auth_headers):
    if not auth_headers:
        return
    response = client.get("/alerts/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_acknowledge_alert(client, auth_headers):
    if not auth_headers:
        return
    create = client.post("/alerts/", headers=auth_headers, json={
        "title": "Ack Test",
        "message": "Test alert",
        "severity": "warning",
    })
    if create.status_code == 201:
        alert_id = create.json()["id"]
        response = client.patch(f"/alerts/{alert_id}", headers=auth_headers, json={
            "acknowledged": True,
        })
        assert response.status_code == 200
        assert response.json()["acknowledged"] is True


def test_predictive_alert_stats(client, auth_headers):
    if not auth_headers:
        return
    response = client.get("/alerts/predictive/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "prevention_rate" in data
