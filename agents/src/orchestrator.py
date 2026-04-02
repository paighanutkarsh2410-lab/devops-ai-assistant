"""
Agent Orchestrator: Coordinates Monitor → Diagnostic → Remediation pipeline.
Listens for events via Redis pub/sub and routes to appropriate agents.
"""
import threading
import time
from monitor_agent import MonitorAgent
from diagnostic_agent import DiagnosticAgent
from remediation_agent import RemediationAgent
from events import (
    subscribe_events, publish_event,
    ANOMALY_DETECTED, INCIDENT_CREATED, DIAGNOSIS_COMPLETE,
    REMEDIATION_STARTED, REMEDIATION_COMPLETE
)
from config import CHECK_INTERVAL_SECONDS


class AgentOrchestrator:
    def __init__(self, dry_run: bool = False):
        self.monitor_agent = MonitorAgent()
        self.diagnostic_agent = DiagnosticAgent()
        self.remediation_agent = RemediationAgent(dry_run=dry_run)
        self._running = False
        self._threads = []
        self._auto_remediation = True
        self._min_confidence = 75  # Min diagnosis confidence to auto-remediate

    def start(self):
        """Start all agents and the event listener."""
        self._running = True

        # Authenticate all agents
        print("[Orchestrator] Authenticating agents...")
        self.monitor_agent.authenticate()
        self.diagnostic_agent.authenticate()
        self.remediation_agent.authenticate()

        # Start Monitor Agent
        monitor_thread = threading.Thread(
            target=self._run_monitor,
            daemon=True,
            name="MonitorAgent"
        )
        monitor_thread.start()
        self._threads.append(monitor_thread)

        # Start Diagnostic Agent
        diag_thread = threading.Thread(
            target=self._run_diagnostic,
            daemon=True,
            name="DiagnosticAgent"
        )
        diag_thread.start()
        self._threads.append(diag_thread)

        # Start Remediation Agent
        rem_thread = threading.Thread(
            target=self._run_remediation,
            daemon=True,
            name="RemediationAgent"
        )
        rem_thread.start()
        self._threads.append(rem_thread)

        # Start event listener
        event_thread = threading.Thread(
            target=self._listen_events,
            daemon=True,
            name="EventListener"
        )
        event_thread.start()
        self._threads.append(event_thread)

        print("[Orchestrator] All agents started")
        print(f"  Monitor Agent:     checking every {CHECK_INTERVAL_SECONDS}s")
        print(f"  Diagnostic Agent:  checking every 60s")
        print(f"  Remediation Agent: checking every 90s")
        print(f"  Auto-remediation:  {'ENABLED' if self._auto_remediation else 'DISABLED'}")
        print(f"  Event listener:    active")
        print()

    def _run_monitor(self):
        """Run Monitor Agent loop."""
        while self._running:
            try:
                self.monitor_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Monitor error: {e}")
                try:
                    self.monitor_agent.authenticate()
                except Exception:
                    pass
            time.sleep(CHECK_INTERVAL_SECONDS)

    def _run_diagnostic(self):
        """Run Diagnostic Agent loop."""
        while self._running:
            try:
                self.diagnostic_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Diagnostic error: {e}")
                try:
                    self.diagnostic_agent.authenticate()
                except Exception:
                    pass
            time.sleep(60)

    def _run_remediation(self):
        """Run Remediation Agent loop."""
        while self._running:
            try:
                if self._auto_remediation:
                    self.remediation_agent.tick()
                else:
                    print("  [RemAgent] Auto-remediation disabled, skipping")
            except Exception as e:
                print(f"[Orchestrator] Remediation error: {e}")
                try:
                    self.remediation_agent.authenticate()
                except Exception:
                    pass
            time.sleep(90)

    def _listen_events(self):
        """Listen for inter-agent events."""
        try:
            subscribe_events(self._handle_event)
        except Exception as e:
            print(f"[Orchestrator] Event listener error: {e}")

    def _handle_event(self, event_type: str, data: dict):
        """Route events to appropriate handlers."""
        if event_type == ANOMALY_DETECTED:
            print(f"[Orchestrator] Anomaly detected, triggering diagnostic...")

        elif event_type == DIAGNOSIS_COMPLETE:
            inc_id = data.get("incident_id", "")
            confidence = data.get("confidence", 0)
            print(f"[Orchestrator] Diagnosis complete for {inc_id} (confidence: {confidence}%)")

            if self._auto_remediation and confidence >= self._min_confidence:
                print(f"[Orchestrator] Triggering auto-remediation...")
                publish_event(REMEDIATION_STARTED, {"incident_id": inc_id})

        elif event_type == REMEDIATION_COMPLETE:
            inc_id = data.get("incident_id", "")
            success = data.get("success", False)
            print(f"[Orchestrator] Remediation {'succeeded' if success else 'failed'} for {inc_id}")

    def stop(self):
        """Stop all agents gracefully."""
        print("\n[Orchestrator] Shutting down...")
        self._running = False
        self.monitor_agent.stop()
        self.diagnostic_agent.stop()
        self.remediation_agent.stop()

    def wait(self):
        """Block until interrupted."""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
