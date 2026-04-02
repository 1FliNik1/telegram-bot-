from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from src.config import settings


class IsAdmin(BaseFilter):
    """Passes only if the sender's Telegram ID is in ADMIN_IDS."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if not settings.admin_ids:
            return False
        user_id = event.from_user.id if event.from_user else None
        return user_id in settings.admin_ids
