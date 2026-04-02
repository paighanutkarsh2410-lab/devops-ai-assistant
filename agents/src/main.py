"""
DevOps AI Agent Orchestrator - Main entry point.
Starts all three agents: Monitor, Diagnostic, Remediation.
"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from config import LOG_LEVEL
from orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)


def main():
    parser = argparse.ArgumentParser(description="DevOps AI Agent Orchestrator")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run in dry-run mode (no real actions)")
    parser.add_argument("--no-remediation", action="store_true",
                        help="Disable auto-remediation")
    args = parser.parse_args()

    print("=" * 50)
    print("  DevOps AI Agent Orchestrator")
    print("  Agents: Monitor | Diagnostic | Remediation")
    if args.dry_run:
        print("  Mode: DRY RUN")
    print("=" * 50)
    print()

    orchestrator = AgentOrchestrator(dry_run=args.dry_run)

    if args.no_remediation:
        orchestrator._auto_remediation = False

    orchestrator.start()
    orchestrator.wait()


if __name__ == "__main__":
    main()
