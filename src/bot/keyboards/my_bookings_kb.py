from __future__ import annotations

from datetime import datetime

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.booking_kb import format_date_long, format_time
from src.db.models.booking import Booking

_STATUS_EMOJI = {
    "confirmed": "✅",
    "pending": "⏳",
}

_NUMS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

CANCEL_THRESHOLD_SECONDS = 2 * 3600  # 2 hours


# ─── Callbacks ───────────────────────────────────────────────────────────────

class CancelBookingCallback(CallbackData, prefix="mb_cancel"):
    booking_id: int


class ConfirmCancelCallback(CallbackData, prefix="mb_ok_cancel"):
    booking_id: int


class AbortCancelCallback(CallbackData, prefix="mb_abort"):
    pass


class RepeatBookingCallback(CallbackData, prefix="mb_repeat"):
    service_id: int
    master_id: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

def booking_datetime(booking: Booking) -> datetime:
    return datetime.combine(booking.timeslot.date, booking.timeslot.start_time)


def can_cancel(booking: Booking) -> bool:
    if booking.timeslot is None:
        return False
    delta = (booking_datetime(booking) - datetime.now()).total_seconds()
    return delta > CANCEL_THRESHOLD_SECONDS


def is_future(booking: Booking) -> bool:
    if booking.timeslot is None:
        return False
    return booking_datetime(booking) > datetime.now()


def format_booking_line(booking: Booking, num: int) -> str:
    num_emoji = _NUMS[num] if num < len(_NUMS) else f"{num + 1}."
    status = _STATUS_EMOJI.get(booking.status.value, "❓")
    date_label = format_date_long(booking.timeslot.date)
    time_label = f"{format_time(booking.timeslot.start_time)}–{format_time(booking.timeslot.end_time)}"
    return (
        f"{num_emoji} <b>{booking.service.name}</b>\n"
        f"   👩 {booking.master.name}  |  📅 {date_label}  |  🕐 {time_label}\n"
        f"   {status} {booking.status.value.capitalize()}"
    )


# ─── Keyboards ───────────────────────────────────────────────────────────────

def bookings_keyboard(bookings: list[Booking]) -> InlineKeyboardMarkup:
    """Row per booking: [❌ Скасувати #N] [🔄 Повторити #N]"""
    builder = InlineKeyboardBuilder()
    for i, b in enumerate(bookings):
        num = i + 1
        if can_cancel(b):
            builder.button(
                text=f"❌ Скасувати #{num}",
                callback_data=CancelBookingCallback(booking_id=b.id),
            )
        builder.button(
            text=f"🔄 Повторити #{num}",
            callback_data=RepeatBookingCallback(service_id=b.service_id, master_id=b.master_id),
        )
        builder.adjust(2 if can_cancel(b) else 1)
    return builder.as_markup()


def confirm_cancel_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так, скасувати", callback_data=ConfirmCancelCallback(booking_id=booking_id))
    builder.button(text="← Назад", callback_data=AbortCancelCallback())
    builder.adjust(2)
    return builder.as_markup()


def no_bookings_keyboard() -> InlineKeyboardMarkup:
    """Shown when user has no bookings."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✂️ Записатись", callback_data="book_from_empty")
    return builder.as_markup()
