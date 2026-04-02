"""
Agent Orchestrator: Coordinates Monitor Agent -> Diagnostic Agent workflow.
Listens for events via Redis pub/sub and routes to appropriate agents.
"""
import threading
import time
from monitor_agent import MonitorAgent
from diagnostic_agent import DiagnosticAgent
from events import (
    subscribe_events, publish_event,
    ANOMALY_DETECTED, INCIDENT_CREATED, DIAGNOSIS_COMPLETE
)
from config import CHECK_INTERVAL_SECONDS


class AgentOrchestrator:
    def __init__(self):
        self.monitor_agent = MonitorAgent()
        self.diagnostic_agent = DiagnosticAgent()
        self._running = False
        self._threads = []

    def start(self):
        """Start all agents and the event listener."""
        self._running = True

        # Authenticate all agents
        print("[Orchestrator] Authenticating agents...")
        self.monitor_agent.authenticate()
        self.diagnostic_agent.authenticate()

        # Start Monitor Agent in background thread
        monitor_thread = threading.Thread(
            target=self._run_monitor,
            daemon=True,
            name="MonitorAgent"
        )
        monitor_thread.start()
        self._threads.append(monitor_thread)

        # Start Diagnostic Agent in background thread
        diag_thread = threading.Thread(
            target=self._run_diagnostic,
            daemon=True,
            name="DiagnosticAgent"
        )
        diag_thread.start()
        self._threads.append(diag_thread)

        # Start event listener
        event_thread = threading.Thread(
            target=self._listen_events,
            daemon=True,
            name="EventListener"
        )
        event_thread.start()
        self._threads.append(event_thread)

        print("[Orchestrator] All agents started")
        print(f"  Monitor Agent: checking every {CHECK_INTERVAL_SECONDS}s")
        print(f"  Diagnostic Agent: checking every 60s")
        print(f"  Event listener: active")
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
            time.sleep(60)  # Check every 60 seconds

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
            # Diagnostic agent will pick it up on next tick
        elif event_type == DIAGNOSIS_COMPLETE:
            print(f"[Orchestrator] Diagnosis complete for incident {data.get('incident_id')}")

    def stop(self):
        """Stop all agents gracefully."""
        print("\n[Orchestrator] Shutting down...")
        self._running = False
        self.monitor_agent.stop()
        self.diagnostic_agent.stop()

    def wait(self):
        """Block until interrupted."""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
