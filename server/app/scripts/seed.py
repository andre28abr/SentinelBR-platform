"""Cria o primeiro usuario admin + a org default se ainda nao existirem.

Uso:
    uv run python -m app.scripts.seed
    SEED_EMAIL=foo@x.com SEED_PASSWORD=segredo SEED_NAME="Foo" uv run python -m app.scripts.seed
    SEED_ORG_NAME="Acme Corp" SEED_ORG_SLUG=acme uv run python -m app.scripts.seed
"""

import asyncio
import os
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Organization, User
from app.services.auth import hash_password


async def seed() -> int:
    email = os.environ.get("SEED_EMAIL", "admin@sentinelbr.io")
    password = os.environ.get("SEED_PASSWORD", "admin1234")  # noqa: S105
    name = os.environ.get("SEED_NAME", "Andre Souza")
    org_name = os.environ.get("SEED_ORG_NAME", "andre28abr")
    org_slug = os.environ.get("SEED_ORG_SLUG", "andre28abr")

    async with SessionLocal() as db:
        # garante org
        org = (
            await db.execute(select(Organization).where(Organization.slug == org_slug))
        ).scalar_one_or_none()
        if org is None:
            org = Organization(name=org_name, slug=org_slug)
            db.add(org)
            await db.commit()
            await db.refresh(org)
            print(f"org criada: id={org.id} name={org.name} slug={org.slug}")
        else:
            print(f"org ja existe: id={org.id} slug={org.slug}")

        # garante user
        existing = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            print(f"ja existe usuario com email {email} (id={existing.id})", file=sys.stderr)
            return 0

        user = User(
            org_id=org.id,
            email=email,
            password_hash=hash_password(password),
            name=name,
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"user criado: id={user.id} email={user.email} senha={'*' * len(password)}")
        if password == "admin1234":
            print("ATENCAO: senha default. Defina SEED_PASSWORD em producao.", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(seed()))
