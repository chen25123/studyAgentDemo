#!/bin/bash
# DevFlow Agent 一键启动脚本
set -e

echo "=== DevFlow Agent ==="

# 1. Check MySQL
echo "[1/4] Checking MySQL..."
mysqladmin ping -h 127.0.0.1 -u root --silent 2>/dev/null || {
    echo "MySQL not running. Start via: net start MySQL80"
    exit 1
}
echo "  MySQL OK"

# 2. Install Python deps
echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt -q

# 3. Run migrations
echo "[3/4] Running Alembic migrations..."
alembic upgrade head

# 4. Start backend
echo "[4/4] Starting backend..."
uvicorn llm.api.app:app --host 127.0.0.1 --port 8010 --reload &
BACKEND_PID=$!

echo ""
echo "=== Ready ==="
echo "Backend: http://127.0.0.1:8010"
echo "Health:  http://127.0.0.1:8010/health"
echo ""
echo "Frontend: cd agent-ui && npm run dev"
echo "Stop: kill $BACKEND_PID"

wait $BACKEND_PID
