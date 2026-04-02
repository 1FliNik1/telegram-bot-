from __future__ import annotations

import contextlib
import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

error_router = Router(name="error_handler")


@error_router.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    """Log all unhandled exceptions and notify the user politely."""
    logger.exception(
        "Unhandled exception in handler %s",
        event.update,
        exc_info=event.exception,
    )

    # Try to reply to the user
    update = event.update
    message = None

    if update.message:
        message = update.message
    elif update.callback_query:
        try:
            await update.callback_query.answer(
                "😔 Сталася помилка. Спробуйте ще раз або почніть з /start.",
                show_alert=True,
            )
        except Exception:
            message = update.callback_query.message

    if message:
        with contextlib.suppress(Exception):
            await message.answer(
                "😔 Сталася технічна помилка. Спробуйте ще раз або натисніть /start."
            )
