#!/bin/bash
# Start the agent orchestrator
# Usage: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting SentryAI Agent Orchestrator..."
echo "  Backend URL: ${BACKEND_URL:-http://localhost:8000}"
echo "  Redis URL:   ${REDIS_URL:-redis://localhost:6379}"
echo "  Log Level:   ${LOG_LEVEL:-INFO}"

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 30); do
    if curl -sf "${BACKEND_URL:-http://localhost:8000}/health" > /dev/null 2>&1; then
        echo "Backend is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "WARNING: Backend not responding, starting anyway..."
    fi
    sleep 2
done

# Start agents
python src/main.py
