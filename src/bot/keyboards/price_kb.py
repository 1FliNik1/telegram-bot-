from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.catalog_kb import CategoryCallback


def price_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Кнопка 'Записатись' під прайсом кожної категорії."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✂️ Записатись",
        callback_data=CategoryCallback(category_id=category_id),
    )
    return builder.as_markup()
