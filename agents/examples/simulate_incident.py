"""
Simulate an incident and trigger diagnostic analysis.
Run: python agents/examples/simulate_incident.py
"""
import sys
import os
import json
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from config import BACKEND_URL, AGENT_EMAIL, AGENT_PASSWORD


def get_token():
    """Login and get auth token."""
    # Signup (ignore if exists)
    requests.post(f"{BACKEND_URL}/auth/signup", json={
        "email": AGENT_EMAIL,
        "password": AGENT_PASSWORD,
        "full_name": "Test Simulator"
    })
    resp = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": AGENT_EMAIL,
        "password": AGENT_PASSWORD
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def main():
    scenario_file = sys.argv[1] if len(sys.argv) > 1 else "test_scenarios/cpu_spike.json"
    scenario_path = os.path.join(os.path.dirname(__file__), scenario_file)

    print(f"Loading scenario: {scenario_file}")
    with open(scenario_path) as f:
        scenario = json.load(f)

    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 1. Create incident
    print("\n1. Creating incident...")
    resp = requests.post(f"{BACKEND_URL}/incidents/", json=scenario["incident"], headers=headers)
    resp.raise_for_status()
    incident = resp.json()
    print(f"   Created: {incident['title']} (id: {incident['id']})")

    # 2. Store metrics
    print("\n2. Storing metrics...")
    metrics = [{"service_name": m["service_name"], "metric_name": m["metric_name"],
                "value": m["value"], "unit": m["unit"]} for m in scenario.get("metrics", [])]
    if metrics:
        resp = requests.post(f"{BACKEND_URL}/metrics/bulk", json={"metrics": metrics}, headers=headers)
        print(f"   Stored {resp.json().get('inserted', 0)} metrics")

    # 3. Store logs
    print("\n3. Storing logs...")
    logs = [{"service_name": scenario["incident"]["service_name"],
             "level": l["level"], "message": l["message"]}
            for l in scenario.get("logs", [])]
    if logs:
        resp = requests.post(f"{BACKEND_URL}/logs/bulk", json={"logs": logs}, headers=headers)
        print(f"   Stored {resp.json().get('inserted', 0)} logs")

    # 4. Store deployments
    print("\n4. Storing deployments...")
    for dep in scenario.get("deployments", []):
        resp = requests.post(f"{BACKEND_URL}/deployments/", json=dep, headers=headers)
        print(f"   Recorded: {dep['service_name']} v{dep['version']}")

    # 5. Run diagnostic
    print("\n5. Running AI diagnostic analysis...")
    from services.llm_service import analyze_incident
    analysis = analyze_incident(
        incident=scenario["incident"],
        metrics=scenario.get("metrics", []),
        logs=scenario.get("logs", []),
        deployments=scenario.get("deployments", [])
    )

    print(f"\n{'='*50}")
    print("DIAGNOSIS RESULTS:")
    print(f"{'='*50}")
    print(f"Root Cause: {analysis.get('root_cause', 'Unknown')}")
    print(f"Confidence: {analysis.get('confidence', 0)}%")
    print(f"Severity:   {analysis.get('severity_assessment', 'unknown')}")
    print(f"Reasoning:  {analysis.get('reasoning', 'N/A')}")
    print(f"\nRecommended Actions:")
    for action in analysis.get("recommended_actions", []):
        print(f"  - {action}")

    print(f"\nExpected Root Cause:")
    print(f"  {scenario.get('expected_root_cause', 'Not specified')}")


if __name__ == "__main__":
    main()
