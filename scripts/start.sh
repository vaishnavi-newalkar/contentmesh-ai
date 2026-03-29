#!/bin/bash
set -e

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║   ContentMesh — AI Content Pipeline   ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3.10+ is required. Please install it first."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_VERSION" -lt 10 ]; then
    echo "❌  Python 3.10+ required. Found 3.$PY_VERSION"
    exit 1
fi

# .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️   Created .env from template."
    echo "    → Open .env and set your ANTHROPIC_API_KEY, then re-run this script."
    echo ""
    exit 0
fi

# Check key is set
if grep -q "your_anthropic_api_key_here" .env; then
    echo "⚠️   ANTHROPIC_API_KEY is not set in .env"
    echo "    The web UI will still work in demo mode (click 'Load Demo Result')"
    echo ""
fi

# Virtual environment
if [ ! -d venv ]; then
    echo "📦  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦  Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "🚀  Starting ContentMesh..."
echo "    Web UI:   http://localhost:8000"
echo "    API docs: http://localhost:8000/docs"
echo "    Health:   http://localhost:8000/health"
echo ""
echo "    Press Ctrl+C to stop."
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000
