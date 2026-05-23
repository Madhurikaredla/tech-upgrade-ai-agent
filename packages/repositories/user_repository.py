"""UserRepository — async data access for the users table."""

from __future__ import annotations

import logfire
from sqlalchemy import select

from packages.db.database import SessionLocal
from packages.db.models import User


class UserRepository:
    async def get_by_phone(self, phone: str) -> User | None:
        try:
            async with SessionLocal() as db:
                result = await db.execute(select(User).where(User.phone == phone))
                return result.scalar_one_or_none()
        except Exception:
            logfire.exception("user_repository.get_by_phone failed", phone=phone)
            return None

    async def get_by_id(self, user_id: int) -> User | None:
        try:
            async with SessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                return result.scalar_one_or_none()
        except Exception:
            logfire.exception("user_repository.get_by_id failed", user_id=user_id)
            return None

    async def create(self, phone: str, password_hash: str) -> User:
        async with SessionLocal() as db:
            user = User(phone=phone, password_hash=password_hash)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

    async def exists(self, phone: str) -> bool:
        user = await self.get_by_phone(phone)
        return user is not None
