"""
Integration test: Full Monitor -> Diagnostic -> Remediation pipeline.
Requires backend running on localhost:8000.
"""
import sys
import os
import json
import requests
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config import BACKEND_URL, AGENT_EMAIL, AGENT_PASSWORD


def get_token():
    """Login and get auth token."""
    requests.post(f"{BACKEND_URL}/auth/signup", json={
        "email": AGENT_EMAIL,
        "password": AGENT_PASSWORD,
        "full_name": "Pipeline Tester"
    })
    resp = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": AGENT_EMAIL,
        "password": AGENT_PASSWORD
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def test_full_pipeline():
    """Run the complete incident lifecycle."""
    print("=" * 50)
    print("  Full Pipeline Integration Test")
    print("=" * 50)

    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Create an incident
    print("\n1. Creating incident...")
    resp = requests.post(f"{BACKEND_URL}/incidents/", json={
        "title": "Pipeline Test: CPU spike on web-server-01",
        "description": "CPU usage exceeded 95% for over 5 minutes",
        "severity": "critical",
        "service_name": "web-server-01"
    }, headers=headers)
    resp.raise_for_status()
    incident = resp.json()
    inc_id = incident["id"]
    print(f"   Created: {incident['title']} (id: {inc_id})")

    # 2. Store some metrics
    print("\n2. Storing metrics...")
    resp = requests.post(f"{BACKEND_URL}/metrics/bulk", json={
        "metrics": [
            {"service_name": "web-server-01", "metric_name": "cpu", "value": 96.5, "unit": "%"},
            {"service_name": "web-server-01", "metric_name": "memory", "value": 72.0, "unit": "%"},
        ]
    }, headers=headers)
    print(f"   Stored {resp.json().get('inserted', 0)} metrics")

    # 3. Create approval request
    print("\n3. Creating approval request...")
    resp = requests.post(f"{BACKEND_URL}/approvals/", json={
        "incident_id": inc_id,
        "action_name": "restart_service",
        "action_description": "Restart web-server-01 to resolve CPU spike",
        "risk_level": "LOW",
    }, headers=headers)
    resp.raise_for_status()
    approval = resp.json()
    print(f"   Approval created: {approval['id']} (status: {approval['status']})")

    # 4. Approve it
    print("\n4. Approving action...")
    resp = requests.post(f"{BACKEND_URL}/approvals/{approval['id']}/approve",
                         json={}, headers=headers)
    resp.raise_for_status()
    print(f"   Status: {resp.json()['status']}")

    # 5. Log remediation action
    print("\n5. Logging remediation action...")
    resp = requests.post(f"{BACKEND_URL}/audit/actions", json={
        "incident_id": inc_id,
        "action_name": "restart_service",
        "action_type": "remediation",
        "executed_by": "RemediationAgent",
        "duration_seconds": 12.5,
        "status": "success",
        "impact_score": 45.0,
        "rollback_performed": False,
    }, headers=headers)
    resp.raise_for_status()
    action_log = resp.json()
    print(f"   Action logged: {action_log['id']}")

    # 6. Check audit stats
    print("\n6. Checking audit stats...")
    resp = requests.get(f"{BACKEND_URL}/audit/stats", headers=headers)
    stats = resp.json()
    print(f"   Total actions: {stats['total_actions']}")
    print(f"   Success rate: {stats['success_rate']}%")

    # 7. Update incident as resolved
    print("\n7. Resolving incident...")
    resp = requests.patch(f"{BACKEND_URL}/incidents/{inc_id}", json={
        "status": "resolved",
        "root_cause": "CPU spike caused by deployment v2.1.0",
        "solution": "Service restarted, monitoring for recurrence",
    }, headers=headers)
    resp.raise_for_status()
    print(f"   Status: {resp.json()['status']}")

    print(f"\n{'=' * 50}")
    print("  Pipeline test PASSED!")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    try:
        test_full_pipeline()
    except requests.ConnectionError:
        print("ERROR: Backend not running. Start it first: cd backend && python src/main.py")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
