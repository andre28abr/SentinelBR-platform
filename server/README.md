# sentinelbr-server

API central. Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 (async) + Celery + Redis.

## Setup

```bash
make setup-server    # uv sync
```

## Run (dev)

```bash
# requer postgres+redis (sobe via `make dev` no root)
make server          # uvicorn em :8000 com reload
# docs: http://localhost:8000/docs
```

## Estrutura

```
server/
├── app/
│   ├── main.py           # entry point FastAPI
│   ├── config.py         # Pydantic Settings (env vars)
│   ├── api/              # routers REST
│   │   └── health.py
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas (request/response)
│   ├── services/         # business logic
│   ├── workers/          # Celery tasks
│   └── db.py             # engine + sessionmaker async
├── tests/
└── pyproject.toml
```
