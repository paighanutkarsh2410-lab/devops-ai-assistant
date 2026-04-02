"""
Example: Memory leak remediation scenario.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from actions.restart_service import RestartServiceAction
from safety.execution_framework import SafeExecutionFramework
from strategies.strategy_selector import StrategySelector


def main():
    print("=" * 50)
    print("  Memory Leak Remediation Scenario")
    print("=" * 50)

    diagnosis = {
        "root_cause": "Memory leak caused by unbounded session cache growth",
        "confidence": 90,
        "severity": "high",
        "service_name": "auth-service",
    }

    selector = StrategySelector()
    strategy = selector.select_strategy(diagnosis)
    print(f"\n1. Strategy: {strategy.name} - {strategy.description}")

    for i, step in enumerate(strategy.steps):
        print(f"   Step {i+1}: {step['action']} (condition: {step['condition']})")

    # Execute first action in dry-run
    framework = SafeExecutionFramework(dry_run=True)
    action = RestartServiceAction()

    print(f"\n2. Executing: {action.name}")
    result = framework.execute_action(action, {"service_name": "auth-service"})
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")

    print(f"\n{'=' * 50}")
    print("  Scenario complete!")


if __name__ == "__main__":
    main()
