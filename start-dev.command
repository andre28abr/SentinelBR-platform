#!/bin/bash
# Double-click esse arquivo no Finder pra subir TODO o ambiente de dev:
#   1. Sobe stack docker (postgres, redis, loki, minio) se ainda nao subiu
#   2. Roda mprocs com server + gRPC + web em paralelo numa unica janela
# Pra parar: tecla `q` dentro do mprocs (mata todos os 3) e/ou rode stop-dev.command

set -e

cd "$(dirname "$0")"

# garante PATH com homebrew (Finder nao herda PATH do shell interativo)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "=== SentinelBR dev ==="
echo

# checagem: docker rodando?
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker nao esta rodando."
    echo "   Abra OrbStack (ou Docker Desktop) e tente de novo."
    echo
    read -n 1 -s -r -p "Pressione qualquer tecla pra fechar..."
    exit 1
fi

# checagem: mprocs instalado?
if ! command -v mprocs > /dev/null; then
    echo "❌ mprocs nao instalado. Rode: brew install mprocs"
    read -n 1 -s -r -p "Pressione qualquer tecla pra fechar..."
    exit 1
fi

# checagem: portas livres?
PORTS_BUSY=$(lsof -ti:5173,8000,9443 2>/dev/null || true)
if [ -n "$PORTS_BUSY" ]; then
    echo "⚠️  Portas 5173/8000/9443 ja em uso. Matando processos antigos..."
    echo "$PORTS_BUSY" | xargs kill 2>/dev/null || true
    sleep 1
fi

# 1. sobe a stack docker (idempotente)
echo "→ Subindo stack docker..."
make dev | tail -8
echo

# 2. abre mprocs com os 3 dev servers
echo "→ Iniciando server + gRPC + web no mprocs..."
echo "  (pra sair: tecla 'q' dentro do mprocs — mata os 3)"
echo
sleep 1

exec mprocs --config mprocs.yaml
