#!/bin/bash
# Quick Start Script - Contract Review Environment

set -e

echo "=================================="
echo "Contract Review Environment v2.0"
echo "Quick Start & Verification"
echo "=================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

# Start server in background
echo ""
echo "✓ Starting FastAPI server..."
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860 &
SERVER_PID=$!

# Wait for server to start
echo "  Waiting for server to initialize..."
sleep 5

# Test endpoints
echo ""
echo "✓ Testing endpoints..."

# Health check
echo "  [1/4] Health check..."
curl -s http://localhost:7860/ | python -m json.tool | head -5

# List tasks
echo ""
echo "  [2/4] List tasks..."
curl -s http://localhost:7860/tasks | python -m json.tool | head -10

# Reset environment
echo ""
echo "  [3/4] Reset environment..."
curl -s -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_detection"}' | python -m json.tool | head -15

# Test step
echo ""
echo "  [4/4] Test step action..."
curl -s -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"type": "request_next_clause"}}' | python -m json.tool | head -15

echo ""
echo "=================================="
echo "✅ All tests passed!"
echo "=================================="
echo ""
echo "Server is running at http://localhost:7860"
echo "API docs: http://localhost:7860/docs"
echo ""
echo "To run inference (requires OPENAI_API_KEY):"
echo "  export OPENAI_API_KEY='sk-...'"
echo "  python inference.py"
echo ""
echo "To stop server: kill $SERVER_PID"
echo ""
