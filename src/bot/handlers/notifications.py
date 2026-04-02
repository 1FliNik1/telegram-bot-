from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from src.bot.keyboards.notification_kb import (
    ReminderCancelCallback,
    ReminderConfirmCallback,
    ReviewCallback,
)
from src.db.base import async_session_factory
from src.db.models.booking import Booking, BookingStatus
from src.db.repositories.booking_repo import BookingRepository
from src.db.repositories.user_repo import UserRepository

router = Router(name="notifications")
logger = logging.getLogger(__name__)


async def _get_booking(session, booking_id: int, telegram_id: int) -> Booking | None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        return None
    booking_repo = BookingRepository(session)
    bookings = await booking_repo.get_user_upcoming_bookings(user.id)
    return next((b for b in bookings if b.id == booking_id), None)


# ─── "✅ Буду!" / "👍 Вже їду!" ─────────────────────────────────────────────

@router.callback_query(ReminderConfirmCallback.filter())
async def on_reminder_confirm(
    callback: CallbackQuery, callback_data: ReminderConfirmCallback
) -> None:
    async with async_session_factory() as session:
        booking = await _get_booking(session, callback_data.booking_id, callback.from_user.id)
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            await session.commit()

    await callback.answer("✅ Чудово! Чекаємо вас!")
    import contextlib
    with contextlib.suppress(Exception):
        await callback.message.edit_reply_markup(reply_markup=None)


# ─── "❌ Скасувати" from reminder ─────────────────────────────────────────────

@router.callback_query(ReminderCancelCallback.filter())
async def on_reminder_cancel(
    callback: CallbackQuery, callback_data: ReminderCancelCallback
) -> None:
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user is None:
            await callback.answer("Користувача не знайдено.", show_alert=True)
            return

        booking_repo = BookingRepository(session)
        success = await booking_repo.cancel_booking(callback_data.booking_id, user.id)
        await session.commit()

    if success:
        await callback.answer("❌ Запис скасовано.")
        await callback.message.edit_text(
            callback.message.text + "\n\n<i>❌ Запис скасовано.</i>",
            reply_markup=None,
        )
    else:
        await callback.answer("Запис вже скасовано або не знайдено.", show_alert=True)


# ─── Review stars ─────────────────────────────────────────────────────────────

@router.callback_query(ReviewCallback.filter())
async def on_review(callback: CallbackQuery, callback_data: ReviewCallback) -> None:
    stars = "⭐" * callback_data.stars
    await callback.answer(f"Дякуємо! {stars}")
    import contextlib
    with contextlib.suppress(Exception):
        await callback.message.edit_text(
            callback.message.text + f"\n\n{stars} Дякуємо за ваш відгук!",
            reply_markup=None,
        )
