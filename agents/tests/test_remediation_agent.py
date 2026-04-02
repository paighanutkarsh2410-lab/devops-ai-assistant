"""Tests for the remediation agent action selection and strategies."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from actions import ACTION_REGISTRY
from actions.restart_service import RestartServiceAction
from actions.scale_service import ScaleServiceAction
from actions.clear_cache import ClearCacheAction
from strategies.strategy_selector import StrategySelector


def test_action_registry():
    """Test all actions are registered."""
    expected = [
        "restart_service", "scale_service", "rollback_deployment",
        "clear_cache", "increase_resources", "kill_process", "adjust_rate_limit",
    ]
    for name in expected:
        assert name in ACTION_REGISTRY, f"Missing action: {name}"
    print("  [PASS] Action registry complete")


def test_restart_action():
    """Test restart service action validation."""
    action = RestartServiceAction()
    assert action.name == "restart_service"
    assert action.risk_level == "LOW"

    valid, msg = action.validate({"service_name": "web-server-01"})
    assert valid

    valid, msg = action.validate({})
    assert not valid
    assert "service_name" in msg

    print("  [PASS] Restart action tests")


def test_scale_action():
    """Test scale service action validation."""
    action = ScaleServiceAction()
    assert action.risk_level == "MEDIUM"

    valid, msg = action.validate({"service_name": "web-01", "target_replicas": 3})
    assert valid

    valid, msg = action.validate({"service_name": "web-01", "target_replicas": 15})
    assert not valid
    assert "10 replicas" in msg

    valid, msg = action.validate({"service_name": "web-01", "target_replicas": 0})
    assert not valid

    print("  [PASS] Scale action tests")


def test_clear_cache_action():
    """Test clear cache action."""
    action = ClearCacheAction()
    assert action.risk_level == "LOW"

    valid, msg = action.validate({})
    assert valid  # Redis available from Day 3 deps

    print("  [PASS] Clear cache action tests")


def test_strategy_selector():
    """Test strategy selection from diagnosis."""
    selector = StrategySelector()

    # Memory leak
    strategy = selector.select_strategy({"root_cause": "Memory leak in auth-service"})
    assert strategy.name == "memory_leak"

    # CPU spike
    strategy = selector.select_strategy({"root_cause": "CPU spike from rogue process"})
    assert strategy.name == "cpu_spike"

    # API timeout
    strategy = selector.select_strategy({"root_cause": "Timeout connecting to upstream"})
    assert strategy.name == "api_timeout"

    # Deployment issue
    strategy = selector.select_strategy({"root_cause": "Bad deployment v2.1.0"})
    assert strategy.name == "deployment_issue"

    # Database
    strategy = selector.select_strategy({"root_cause": "Slow SQL query on metrics table"})
    assert strategy.name == "database_slow"

    # Unknown (defaults to generic restart)
    strategy = selector.select_strategy({"root_cause": "Unknown issue"})
    assert strategy.name == "generic_restart"

    print("  [PASS] Strategy selector tests")


def test_action_select_from_diagnosis():
    """Test the diagnosis-to-action mapping."""
    from remediation_agent import DIAGNOSIS_ACTION_MAP

    text = "memory leak causing oom errors"
    matched = [a for kw, a in DIAGNOSIS_ACTION_MAP.items() if kw in text.lower()]
    assert "restart_service" in matched

    text = "high cpu spike on web server"
    matched = [a for kw, a in DIAGNOSIS_ACTION_MAP.items() if kw in text.lower()]
    assert "scale_service" in matched

    text = "bad deployment caused errors"
    matched = [a for kw, a in DIAGNOSIS_ACTION_MAP.items() if kw in text.lower()]
    assert "rollback_deployment" in matched

    print("  [PASS] Diagnosis-to-action mapping tests")


if __name__ == "__main__":
    print("Running remediation agent tests...\n")
    test_action_registry()
    test_restart_action()
    test_scale_action()
    test_clear_cache_action()
    test_strategy_selector()
    test_action_select_from_diagnosis()
    print("\nAll remediation agent tests passed!")
