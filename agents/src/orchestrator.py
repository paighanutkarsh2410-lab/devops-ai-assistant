"""
Agent Orchestrator: Coordinates Monitor → Diagnostic → Remediation → Learn → Predict → Communicate pipeline.
Listens for events via Redis pub/sub and routes to appropriate agents.
"""
import threading
import time
from monitor_agent import MonitorAgent
from diagnostic_agent import DiagnosticAgent
from remediation_agent import RemediationAgent
from learning_agent import LearningAgent
from prediction_agent import PredictionAgent
from communication_agent import CommunicationAgent
from log_analysis_agent import LogAnalysisAgent
from capacity_planning_agent import CapacityPlanningAgent
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
        self.learning_agent = LearningAgent()
        self.prediction_agent = PredictionAgent()
        self.communication_agent = CommunicationAgent()
        self.log_analysis_agent = LogAnalysisAgent()
        self.capacity_planning_agent = CapacityPlanningAgent()
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
        self.learning_agent.authenticate()
        self.prediction_agent.authenticate()
        self.communication_agent.authenticate()
        self.log_analysis_agent.authenticate()
        self.capacity_planning_agent.authenticate()

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

        # Start Learning Agent
        learn_thread = threading.Thread(
            target=self._run_learning,
            daemon=True,
            name="LearningAgent"
        )
        learn_thread.start()
        self._threads.append(learn_thread)

        # Start Prediction Agent (hourly)
        pred_thread = threading.Thread(
            target=self._run_prediction,
            daemon=True,
            name="PredictionAgent"
        )
        pred_thread.start()
        self._threads.append(pred_thread)

        # Start Communication Agent (every 5 min for daily summary check)
        comm_thread = threading.Thread(
            target=self._run_communication,
            daemon=True,
            name="CommunicationAgent"
        )
        comm_thread.start()
        self._threads.append(comm_thread)

        # Start Log Analysis Agent (every 2 min)
        log_thread = threading.Thread(
            target=self._run_log_analysis,
            daemon=True,
            name="LogAnalysisAgent"
        )
        log_thread.start()
        self._threads.append(log_thread)

        # Start Capacity Planning Agent (every 30 min)
        cap_thread = threading.Thread(
            target=self._run_capacity_planning,
            daemon=True,
            name="CapacityPlanningAgent"
        )
        cap_thread.start()
        self._threads.append(cap_thread)

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
        print(f"  Learning Agent:    checking every 120s")
        print(f"  Prediction Agent:  checking every 3600s")
        print(f"  Comms Agent:       checking every 300s")
        print(f"  Log Analysis:      checking every 120s")
        print(f"  Capacity Planning: checking every 1800s")
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

    def _run_learning(self):
        """Run Learning Agent loop."""
        while self._running:
            try:
                self.learning_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Learning error: {e}")
                try:
                    self.learning_agent.authenticate()
                except Exception:
                    pass
            time.sleep(120)

    def _run_prediction(self):
        """Run Prediction Agent loop (hourly)."""
        while self._running:
            try:
                self.prediction_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Prediction error: {e}")
                try:
                    self.prediction_agent.authenticate()
                except Exception:
                    pass
            time.sleep(3600)

    def _run_communication(self):
        """Run Communication Agent loop (every 5 min)."""
        while self._running:
            try:
                self.communication_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Communication error: {e}")
                try:
                    self.communication_agent.authenticate()
                except Exception:
                    pass
            time.sleep(300)

    def _run_log_analysis(self):
        """Run Log Analysis Agent loop (every 2 min)."""
        while self._running:
            try:
                self.log_analysis_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Log Analysis error: {e}")
                try:
                    self.log_analysis_agent.authenticate()
                except Exception:
                    pass
            time.sleep(120)

    def _run_capacity_planning(self):
        """Run Capacity Planning Agent loop (every 30 min)."""
        while self._running:
            try:
                self.capacity_planning_agent.tick()
            except Exception as e:
                print(f"[Orchestrator] Capacity Planning error: {e}")
                try:
                    self.capacity_planning_agent.authenticate()
                except Exception:
                    pass
            time.sleep(1800)

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
            try:
                self.communication_agent.handle_incident_detected(data)
            except Exception as e:
                print(f"[Orchestrator] Notification failed: {e}")

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

            try:
                self.communication_agent.handle_remediation_completed(
                    inc_id, data.get("action_name", "unknown"), success, data
                )
            except Exception as e:
                print(f"[Orchestrator] Notification failed: {e}")

            # Trigger learning from the resolved incident
            if success:
                print(f"[Orchestrator] Triggering learning for {inc_id}...")
                try:
                    incident = self.learning_agent.api_get(f"/incidents/{inc_id}")
                    if incident:
                        self.learning_agent.learn_from_incident(incident)
                except Exception as e:
                    print(f"[Orchestrator] Learning trigger failed: {e}")

    def stop(self):
        """Stop all agents gracefully."""
        print("\n[Orchestrator] Shutting down...")
        self._running = False
        self.monitor_agent.stop()
        self.diagnostic_agent.stop()
        self.remediation_agent.stop()
        self.learning_agent.stop()
        self.prediction_agent.stop()
        self.communication_agent.stop()
        self.log_analysis_agent.stop()
        self.capacity_planning_agent.stop()

    def wait(self):
        """Block until interrupted."""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
