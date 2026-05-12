import asyncio
import os
from collections.abc import AsyncGenerator

# Setar env vars ANTES de importar app.config — evita assert do JWT_SECRET
# falhar em CI sem env, e garante que testes nao usam o default real.
os.environ.setdefault("SENTINELBR_JWT_SECRET", "test-jwt-secret-32-bytes-mininum-len")
os.environ.setdefault("SENTINELBR_DEBUG", "true")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Organization, User  # noqa: E402
from app.services.auth import hash_password  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    base, _ = settings.database_url.rsplit("/", 1)
    test_url = f"{base}/sentinelbr_test"

    admin_url = f"{base}/postgres"
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.exec_driver_sql("DROP DATABASE IF EXISTS sentinelbr_test")
        await conn.exec_driver_sql("CREATE DATABASE sentinelbr_test")
    await admin_engine.dispose()

    engine = create_async_engine(test_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def default_org(db_session: AsyncSession) -> Organization:
    org = Organization(name="Test Org", slug="test")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, default_org: Organization) -> User:
    user = User(
        org_id=default_org.id,
        email="admin@test.io",
        password_hash=hash_password("teste1234"),
        name="Admin Teste",
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
