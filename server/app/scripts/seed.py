"""Cria o primeiro usuario admin se ainda nao existir.

Uso:
    uv run python -m app.scripts.seed
    SEED_EMAIL=foo@x.com SEED_PASSWORD=segredo SEED_NAME="Foo" uv run python -m app.scripts.seed
"""

import asyncio
import os
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User
from app.services.auth import hash_password


async def seed() -> int:
    email = os.environ.get("SEED_EMAIL", "admin@sentinelbr.io")
    password = os.environ.get("SEED_PASSWORD", "admin1234")
    name = os.environ.get("SEED_NAME", "Admin")

    async with SessionLocal() as db:
        existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if existing is not None:
            print(f"ja existe usuario com email {email} (id={existing.id})", file=sys.stderr)
            return 0

        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        print(f"criado: id={user.id} email={user.email} senha={'*' * len(password)}")
        if password == "admin1234":
            print("ATENCAO: senha default. Defina SEED_PASSWORD em producao.", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(seed()))
