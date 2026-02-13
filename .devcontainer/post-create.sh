#!/bin/bash
# Post-create script for SYMBIONT-X devcontainer
set -e

echo "🚀 Setting up SYMBIONT-X development environment..."

# Update pip
echo "📦 Updating pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    pre-commit install --hook-type commit-msg
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
if [ -d "src/frontend" ]; then
    cd src/frontend
    npm install
    cd ../..
fi

# Configure git
echo "🔧 Configuring git..."
git config --global --add safe.directory /workspaces/SYMBIONT-X

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p .pytest_cache
mkdir -p htmlcov

# Azure CLI login check
echo "☁️ Azure CLI status..."
if az account show &> /dev/null; then
    echo "✅ Azure CLI already authenticated"
else
    echo "⚠️  Run 'az login' to authenticate with Azure"
fi

# GitHub CLI login check
echo "🐙 GitHub CLI status..."
if gh auth status &> /dev/null; then
    echo "✅ GitHub CLI already authenticated"
else
    echo "⚠️  Run 'gh auth login' to authenticate with GitHub"
fi

echo ""
echo "✅ Development environment ready!"
echo ""
echo "📝 Next steps:"
echo "  1. Run 'az login' if not authenticated"
echo "  2. Run 'gh auth login' if not authenticated"
echo "  3. Copy .env.example to .env and fill in values"
echo "  4. Run 'make test' to verify setup"
echo ""
