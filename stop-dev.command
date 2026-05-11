#!/bin/bash
# Double-click pra parar tudo: dev servers + docker stack.

cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "=== Parando SentinelBR dev ==="

echo "→ Matando server/gRPC/web (portas 5173/8000/9443)..."
lsof -ti:5173,8000,9443 2>/dev/null | xargs kill 2>/dev/null || true
pkill -f 'app.grpc_server.server' 2>/dev/null || true
pkill -f 'uvicorn app.main' 2>/dev/null || true
pkill -f 'vite' 2>/dev/null || true

echo "→ Derrubando stack docker..."
make dev-down 2>&1 | tail -5

echo
echo "✓ Tudo parado."
sleep 2
