#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================="
echo "  个人彩瞳管理平台 - 启动脚本"
echo "  前端: http://localhost:9101"
echo "  后端: http://localhost:9102"
echo "=========================================="
echo ""

echo "Starting backend server on port 9102..."
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && bash start-backend.sh"'

sleep 2

echo "Starting frontend server on port 9101..."
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && bash start-frontend.sh"'

echo ""
echo "Servers are starting in separate Terminal windows."
echo "Please wait a moment for them to fully initialize."
