"""Test incidents CRUD endpoints."""


def test_create_incident(client, auth_headers):
    if not auth_headers:
        return
    response = client.post("/incidents/", headers=auth_headers, json={
        "title": "Test CPU Spike",
        "severity": "high",
        "service_name": "api-server",
        "description": "CPU at 95%",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test CPU Spike"
    assert data["severity"] == "high"
    assert data["status"] == "open"


def test_list_incidents(client, auth_headers):
    if not auth_headers:
        return
    response = client.get("/incidents/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_filter_incidents_by_status(client, auth_headers):
    if not auth_headers:
        return
    response = client.get("/incidents/?status=open", headers=auth_headers)
    assert response.status_code == 200
    for inc in response.json():
        assert inc["status"] == "open"


def test_get_single_incident(client, auth_headers):
    if not auth_headers:
        return
    # Create one first
    create = client.post("/incidents/", headers=auth_headers, json={
        "title": "Single Test",
        "severity": "medium",
    })
    if create.status_code == 201:
        inc_id = create.json()["id"]
        response = client.get(f"/incidents/{inc_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Single Test"


def test_update_incident(client, auth_headers):
    if not auth_headers:
        return
    create = client.post("/incidents/", headers=auth_headers, json={
        "title": "Update Test",
        "severity": "low",
    })
    if create.status_code == 201:
        inc_id = create.json()["id"]
        response = client.patch(f"/incidents/{inc_id}", headers=auth_headers, json={
            "status": "resolved",
            "root_cause": "Memory leak fixed",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"


def test_delete_incident(client, auth_headers):
    if not auth_headers:
        return
    create = client.post("/incidents/", headers=auth_headers, json={
        "title": "Delete Test",
        "severity": "low",
    })
    if create.status_code == 201:
        inc_id = create.json()["id"]
        response = client.delete(f"/incidents/{inc_id}", headers=auth_headers)
        assert response.status_code == 200
