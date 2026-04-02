from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ReminderConfirmCallback(CallbackData, prefix="rem_ok"):
    booking_id: int


class ReminderCancelCallback(CallbackData, prefix="rem_cancel"):
    booking_id: int


class ReviewCallback(CallbackData, prefix="review"):
    booking_id: int
    stars: int  # 1-5


def reminder_24h_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Буду!", callback_data=ReminderConfirmCallback(booking_id=booking_id))
    builder.button(text="❌ Скасувати", callback_data=ReminderCancelCallback(booking_id=booking_id))
    builder.adjust(2)
    return builder.as_markup()


def reminder_2h_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👍 Вже їду!", callback_data=ReminderConfirmCallback(booking_id=booking_id))
    builder.adjust(1)
    return builder.as_markup()


def review_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for stars in range(1, 6):
        builder.button(
            text="⭐" * stars,
            callback_data=ReviewCallback(booking_id=booking_id, stars=stars),
        )
    builder.adjust(5)
    return builder.as_markup()
