"""
Agent Runner: Starts the Orchestrator which manages all agents.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import AgentOrchestrator


def main():
    print("=" * 50)
    print("  DevOps AI Assistant - Agent System")
    print("=" * 50)
    print()

    orchestrator = AgentOrchestrator()
    orchestrator.start()
    orchestrator.wait()


if __name__ == "__main__":
    main()
