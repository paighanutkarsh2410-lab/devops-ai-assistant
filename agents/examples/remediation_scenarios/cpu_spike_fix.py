"""
Example: CPU spike remediation scenario.
Simulates a CPU spike incident and runs the remediation pipeline.
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from actions.restart_service import RestartServiceAction
from actions.scale_service import ScaleServiceAction
from safety.execution_framework import SafeExecutionFramework
from strategies.strategy_selector import StrategySelector


def main():
    print("=" * 50)
    print("  CPU Spike Remediation Scenario")
    print("=" * 50)

    # Simulated diagnosis
    diagnosis = {
        "root_cause": "CPU spike caused by deployment v2.1.0 introducing infinite loop",
        "confidence": 85,
        "severity": "critical",
        "service_name": "web-server-01",
    }

    # Step 1: Select strategy
    selector = StrategySelector()
    strategy = selector.select_strategy(diagnosis)
    print(f"\n1. Strategy selected: {strategy.name}")
    print(f"   Description: {strategy.description}")
    print(f"   Steps: {len(strategy.steps)}")

    # Step 2: Get first action
    first_step = selector.get_first_action(strategy)
    print(f"\n2. First action: {first_step['action']}")

    # Step 3: Execute in dry-run mode
    framework = SafeExecutionFramework(dry_run=True)
    action_class = RestartServiceAction if first_step['action'] == 'restart_service' else ScaleServiceAction
    action = action_class()

    print(f"\n3. Executing: {action.name} (risk: {action.risk_level})")
    result = framework.execute_action(action, {
        "service_name": "web-server-01",
        **first_step.get("params", {})
    })

    print(f"\n4. Result:")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    print(f"   Duration: {result.duration_seconds:.2f}s")

    print(f"\n{'=' * 50}")
    print("  Scenario complete!")


if __name__ == "__main__":
    main()
