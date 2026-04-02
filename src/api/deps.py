from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import parse_authorization
from src.db.base import async_session_factory
from src.db.models.user import User
from src.db.repositories.user_repo import UserRepository


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_tg_user(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """Validate Authorization header and return parsed Telegram user dict."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        )
    parsed = parse_authorization(authorization)
    tg_user = parsed.get("user", {})
    if not tg_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_init_data"},
        )
    return tg_user


async def get_db_user(
    tg_user: Dict[str, Any] = Depends(get_tg_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Upsert user in DB and return the ORM User instance."""
    async with session.begin():
        repo = UserRepository(session)
        user = await repo.upsert(
            telegram_id=int(tg_user["id"]),
            first_name=tg_user.get("first_name", ""),
            username=tg_user.get("username"),
            last_name=tg_user.get("last_name"),
        )
    return user
