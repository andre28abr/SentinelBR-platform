.DEFAULT_GOAL := help

SHELL := /bin/bash

GO       ?= go
PYTHON   ?= python3
UV       ?= uv
PNPM     ?= pnpm
PROTOC   ?= protoc
DC       ?= docker compose

AGENT_DIR  := agent
SERVER_DIR := server
WEB_DIR    := web
PROTO_DIR  := proto
DEPLOY_DIR := deploy

VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)

.PHONY: help
help: ## mostra essa ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ─── Setup ────────────────────────────────────────────────────────────────────

.PHONY: setup
setup: setup-server setup-web setup-agent ## instala deps de todos os componentes

.PHONY: setup-agent
setup-agent: ## baixa modules do agente
	cd $(AGENT_DIR) && $(GO) mod download

.PHONY: setup-server
setup-server: ## cria venv e instala deps do server (uv)
	cd $(SERVER_DIR) && $(UV) sync

.PHONY: setup-web
setup-web: ## instala deps do web (pnpm)
	cd $(WEB_DIR) && $(PNPM) install

# ─── Build ────────────────────────────────────────────────────────────────────

.PHONY: agent
agent: ## builda agente para o OS host
	cd $(AGENT_DIR) && $(GO) build -ldflags "-X main.version=$(VERSION)" -o bin/sentinel-agent ./cmd/sentinel-agent

.PHONY: agent-cross
agent-cross: ## cross-compila agente para linux/darwin/windows (amd64+arm64)
	cd $(AGENT_DIR) && \
	  GOOS=linux   GOARCH=amd64 $(GO) build -o bin/sentinel-agent-linux-amd64   ./cmd/sentinel-agent && \
	  GOOS=linux   GOARCH=arm64 $(GO) build -o bin/sentinel-agent-linux-arm64   ./cmd/sentinel-agent && \
	  GOOS=darwin  GOARCH=arm64 $(GO) build -o bin/sentinel-agent-darwin-arm64  ./cmd/sentinel-agent && \
	  GOOS=darwin  GOARCH=amd64 $(GO) build -o bin/sentinel-agent-darwin-amd64  ./cmd/sentinel-agent && \
	  GOOS=windows GOARCH=amd64 $(GO) build -o bin/sentinel-agent-windows-amd64.exe ./cmd/sentinel-agent

# ─── Dev ──────────────────────────────────────────────────────────────────────

.PHONY: dev
dev: ## sobe stack de dev (postgres, redis, loki, minio, server)
	cd $(DEPLOY_DIR) && $(DC) -f compose/docker-compose.dev.yml up -d
	@echo ""
	@echo "Server:    http://localhost:8000/docs"
	@echo "MinIO:     http://localhost:9001 (admin/minioadmin)"
	@echo "Postgres:  localhost:5432 (sentinelbr/sentinelbr)"
	@echo "Loki:      http://localhost:3100"

.PHONY: dev-down
dev-down: ## derruba stack de dev
	cd $(DEPLOY_DIR) && $(DC) -f compose/docker-compose.dev.yml down

.PHONY: web
web: ## roda vite dev server
	cd $(WEB_DIR) && $(PNPM) dev

.PHONY: server
server: ## roda fastapi local (sem docker, precisa de db rodando via `make dev`)
	cd $(SERVER_DIR) && $(UV) run uvicorn app.main:app --reload --port 8000

# ─── Quality ──────────────────────────────────────────────────────────────────

.PHONY: lint
lint: lint-agent lint-server lint-web ## roda linters em todos componentes

.PHONY: lint-agent
lint-agent:
	cd $(AGENT_DIR) && $(GO) vet ./... && $(GO) fmt ./...

.PHONY: lint-server
lint-server:
	cd $(SERVER_DIR) && $(UV) run ruff check . && $(UV) run mypy app

.PHONY: lint-web
lint-web:
	cd $(WEB_DIR) && $(PNPM) lint

.PHONY: test
test: test-agent test-server test-web ## roda testes em todos componentes

.PHONY: test-agent
test-agent:
	cd $(AGENT_DIR) && $(GO) test -race -coverprofile=coverage.out ./...

.PHONY: test-server
test-server:
	cd $(SERVER_DIR) && $(UV) run pytest

.PHONY: test-web
test-web:
	cd $(WEB_DIR) && $(PNPM) test

# ─── Proto ────────────────────────────────────────────────────────────────────

.PHONY: proto
proto: ## regera código a partir dos .proto
	@mkdir -p $(PROTO_DIR)/gen/go $(PROTO_DIR)/gen/python
	$(PROTOC) -I=$(PROTO_DIR) \
	  --go_out=$(PROTO_DIR)/gen/go --go_opt=paths=source_relative \
	  --go-grpc_out=$(PROTO_DIR)/gen/go --go-grpc_opt=paths=source_relative \
	  --python_out=$(PROTO_DIR)/gen/python \
	  --grpc_python_out=$(PROTO_DIR)/gen/python \
	  $(PROTO_DIR)/*.proto

# ─── Clean ────────────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## limpa artefatos de build
	rm -rf $(AGENT_DIR)/bin $(AGENT_DIR)/dist
	rm -rf $(SERVER_DIR)/.venv $(SERVER_DIR)/.pytest_cache $(SERVER_DIR)/.mypy_cache $(SERVER_DIR)/.ruff_cache
	rm -rf $(WEB_DIR)/node_modules $(WEB_DIR)/dist
	rm -rf $(PROTO_DIR)/gen
