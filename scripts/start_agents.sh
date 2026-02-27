#!/bin/bash
# Start all SYMBIONT-X agents in background

echo "🚀 Starting SYMBIONT-X Agents..."

# Activate venv
source venv/bin/activate

# Start agents in background
echo "Starting Orchestrator (port 8000)..."
cd src/agents/orchestrator && python main.py &
ORCH_PID=$!

sleep 2

echo "Starting Security Scanner (port 8001)..."
cd ../security-scanner && python main.py &
SCAN_PID=$!

sleep 2

echo "Starting Risk Assessment (port 8002)..."
cd ../risk-assessment && python main.py &
RISK_PID=$!

sleep 2

echo "Starting Auto-Remediation (port 8003)..."
cd ../auto-remediation && python main.py &
REM_PID=$!

echo ""
echo "✅ All agents started!"
echo ""
echo "PIDs:"
echo "  Orchestrator:     $ORCH_PID"
echo "  Security Scanner: $SCAN_PID"
echo "  Risk Assessment:  $RISK_PID"
echo "  Auto-Remediation: $REM_PID"
echo ""
echo "To stop: kill $ORCH_PID $SCAN_PID $RISK_PID $REM_PID"
echo ""

# Wait for all
wait
