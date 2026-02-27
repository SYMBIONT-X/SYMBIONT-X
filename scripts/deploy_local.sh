#!/bin/bash
# SYMBIONT-X Local Deployment Script
# This script sets up everything from scratch

set -e  # Exit on error

echo "🚀 SYMBIONT-X Deployment Script"
echo "================================"
echo ""

START_TIME=$(date +%s)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Step 1: Check prerequisites
step "Checking prerequisites..."
python3 --version || { echo "Python 3 not found"; exit 1; }
node --version || { echo "Node.js not found"; exit 1; }
npm --version || { echo "npm not found"; exit 1; }
success "Prerequisites OK"

# Step 2: Setup Python environment
step "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
success "Virtual environment activated"

# Step 3: Install Python dependencies
step "Installing Python dependencies..."
pip install -r requirements.txt -q
success "Python dependencies installed"

# Step 4: Install frontend dependencies
step "Installing frontend dependencies..."
cd src/frontend
npm install --silent
cd ../..
success "Frontend dependencies installed"

# Step 5: Run tests
step "Running tests..."
cd src/agents/security-scanner && python -m pytest tests/ -q 2>/dev/null
cd ../../..
cd src/agents/risk-assessment && python -m pytest tests/ -q 2>/dev/null
cd ../../..
cd src/agents/auto-remediation && python -m pytest tests/ -q 2>/dev/null
cd ../../..
cd src/agents/orchestrator && python -m pytest tests/ -q 2>/dev/null
cd ../../..
success "All tests passed"

# Step 6: Build frontend
step "Building frontend..."
cd src/frontend
npm run build --silent
cd ../..
success "Frontend built"

# Calculate time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "================================"
echo "🎉 Deployment Complete!"
echo "================================"
echo "Time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "To start the system:"
echo "  1. Start agents: ./scripts/start_agents.sh"
echo "  2. Start frontend: cd src/frontend && npm run dev"
echo "  3. Open: http://localhost:5173"
echo ""
