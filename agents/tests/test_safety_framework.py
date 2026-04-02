"""Tests for the safety execution framework."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from safety.safety_rules import SafetyRules
from safety.checkpoint import CheckpointManager
from safety.execution_framework import SafeExecutionFramework


def test_safety_rules():
    """Test safety rules enforcement."""
    rules = SafetyRules()

    # Should allow normal actions
    can, reason = rules.can_execute("restart_service", "web-server-01")
    assert can, f"Should allow restart: {reason}"

    # Should require approval for critical services
    assert rules.requires_approval("restart_service", "payment-api")
    assert rules.requires_approval("restart_service", "database-primary")

    # Should not require approval for normal services
    assert not rules.requires_approval("restart_service", "web-server-01")

    # Should require approval for high-risk actions
    assert rules.requires_approval("kill_process", "web-server-01")

    # Risk level check
    assert rules.get_risk_level("restart_service") == "LOW"
    assert rules.get_risk_level("kill_process") == "HIGH"
    assert rules.is_risk_level_allowed("restart_service")

    print("  [PASS] Safety rules tests")


def test_restart_limit():
    """Test max restarts per hour enforcement."""
    rules = SafetyRules()

    # Record 3 restarts
    for _ in range(3):
        rules.record_action("restart_service", "web-server-01", success=True)

    # Should block 4th restart
    can, reason = rules.can_execute("restart_service", "web-server-01")
    assert not can, "Should block after max restarts"
    assert "Max restarts" in reason

    print("  [PASS] Restart limit tests")


def test_checkpoint_manager():
    """Test checkpoint creation and restoration."""
    import tempfile
    mgr = CheckpointManager(storage_dir=tempfile.mkdtemp())

    # Create checkpoint
    ctx = {"metrics": {"cpu": 45}, "version": "1.0", "replicas": 2}
    chk_id = mgr.create_checkpoint("test-service", ctx)
    assert chk_id.startswith("chk_test-service_")

    # Get checkpoint
    data = mgr.get_checkpoint(chk_id)
    assert data["service"] == "test-service"
    assert data["state"]["version"] == "1.0"

    # Restore checkpoint
    state = mgr.restore_checkpoint(chk_id)
    assert state["replicas"] == 2

    # List checkpoints
    checkpoints = mgr.list_checkpoints("test-service")
    assert len(checkpoints) == 1

    print("  [PASS] Checkpoint manager tests")


def test_circuit_breaker():
    """Test circuit breaker stops after consecutive failures."""
    framework = SafeExecutionFramework(dry_run=True)
    framework._consecutive_failures = 3

    class FakeAction:
        name = "test_action"

    result = framework.execute_action(FakeAction(), {"service_name": "test"})
    assert not result.success
    assert "Circuit breaker" in result.message

    # Reset
    framework.reset_circuit_breaker()
    assert framework._consecutive_failures == 0

    print("  [PASS] Circuit breaker tests")


def test_dry_run():
    """Test dry run mode."""
    framework = SafeExecutionFramework(dry_run=True)

    class FakeAction:
        name = "restart_service"

    result = framework.execute_action(FakeAction(), {"service_name": "web-server-01"})
    assert result.success
    assert "Dry run" in result.message

    print("  [PASS] Dry run tests")


if __name__ == "__main__":
    print("Running safety framework tests...\n")
    test_safety_rules()
    test_restart_limit()
    test_checkpoint_manager()
    test_circuit_breaker()
    test_dry_run()
    print("\nAll safety framework tests passed!")
