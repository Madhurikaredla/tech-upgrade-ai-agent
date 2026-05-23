"""Seed default admin user on first startup.

Default credentials:
  Phone    : 8291673037
  Password : 123456
"""

import logfire
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


async def seed_default_user(session: AsyncSession) -> None:
    from packages.auth.service import hash_password

    existing = await session.execute(select(User).where(User.phone == "8291673037"))
    if existing.scalar_one_or_none():
        return

    user = User(
        phone="8291673037",
        password_hash=hash_password("123456"),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    logfire.info("default admin user seeded", phone="8291673037")
