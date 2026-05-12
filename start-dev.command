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

# checagem: docker rodando? Se OrbStack instalado, tenta acordar antes de desistir.
if ! docker info > /dev/null 2>&1; then
    if command -v orb > /dev/null && command -v orbctl > /dev/null; then
        echo "→ Docker engine parado. Acordando OrbStack..."
        orb start > /dev/null 2>&1 || true
        # OrbStack costuma levar 1-3s pra Docker ficar pronto
        for i in $(seq 1 15); do
            if docker info > /dev/null 2>&1; then
                echo "  ✓ Docker pronto"
                break
            fi
            sleep 1
        done
    fi
fi
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker nao esta rodando."
    echo "   Abra OrbStack (ou Docker Desktop) manualmente e tente de novo."
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

# 2. abre browser automaticamente quando Vite estiver pronto (espera ate 30s).
#    Roda em background pra nao travar o mprocs que vem em seguida.
(
    for i in $(seq 1 60); do
        if lsof -nP -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
            sleep 1   # vite escutando, aguarda servir o HTML
            open http://localhost:5173
            break
        fi
        sleep 0.5
    done
) &

# 3. abre mprocs com server + gRPC + web + worker + beat
echo "→ Iniciando server + gRPC + web + worker + beat no mprocs..."
echo "  Browser vai abrir sozinho em ~5s, no http://localhost:5173"
echo "  Pra sair: tecla 'q' dentro do mprocs (mata todos)"
echo
sleep 1

exec mprocs --config mprocs.yaml
