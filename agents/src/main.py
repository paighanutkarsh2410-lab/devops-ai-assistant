"""
Agent Runner: Starts the Monitor Agent.
"""
import sys
import os

# Add agent src to path
sys.path.insert(0, os.path.dirname(__file__))

from monitor_agent import MonitorAgent
from config import CHECK_INTERVAL_SECONDS


def main():
    print("=" * 50)
    print("  DevOps AI Assistant - Monitor Agent")
    print("=" * 50)
    print(f"  Check interval: {CHECK_INTERVAL_SECONDS}s")
    print()

    agent = MonitorAgent()
    try:
        agent.run(interval=CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nShutting down Monitor Agent...")
        agent.stop()


if __name__ == "__main__":
    main()
