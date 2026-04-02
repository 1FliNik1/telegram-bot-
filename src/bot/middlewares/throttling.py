from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

# Per-user bucket: {user_id: [timestamp, ...]}
_buckets: dict[int, list[float]] = defaultdict(list)

WINDOW_SECONDS = 5   # sliding window
MAX_REQUESTS = 5     # max messages per window


class ThrottlingMiddleware(BaseMiddleware):
    """Reject messages from users who send more than MAX_REQUESTS in WINDOW_SECONDS."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        bucket = _buckets[user_id]

        # Remove timestamps outside the window
        _buckets[user_id] = [t for t in bucket if now - t < WINDOW_SECONDS]

        if len(_buckets[user_id]) >= MAX_REQUESTS:
            await event.answer(
                "⏳ Забагато запитів. Зачекайте кілька секунд."
            )
            return None

        _buckets[user_id].append(now)
        return await handler(event, data)
