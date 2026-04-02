from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.bot.keyboards.notification_kb import (
    reminder_2h_keyboard,
    reminder_24h_keyboard,
    review_keyboard,
)
from src.db.base import async_session_factory
from src.db.models.booking import Booking, BookingStatus

logger = logging.getLogger(__name__)

# ─── Time windows ─────────────────────────────────────────────────────────────
# Jobs run every 15 min → windows are slightly wider to avoid missing a booking
_24H_WINDOW = timedelta(hours=24, minutes=15)
_2H_WINDOW = timedelta(hours=2, minutes=15)
_REVIEW_DELAY = timedelta(hours=2)  # send review request 2h after appointment end


# ─── DB helpers ───────────────────────────────────────────────────────────────

async def _load_bookings(
    *,
    flag_column,
    statuses: list[BookingStatus],
) -> list[Booking]:
    """Fetch active bookings where a given reminder flag is False."""
    stmt = (
        select(Booking)
        .options(
            joinedload(Booking.timeslot),
            joinedload(Booking.service),
            joinedload(Booking.master),
            joinedload(Booking.user),
        )
        .where(flag_column.is_(False))
        .where(Booking.status.in_(statuses))
    )
    async with async_session_factory() as session:
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())


def _slot_start(b: Booking) -> datetime:
    return datetime.combine(b.timeslot.date, b.timeslot.start_time)


def _slot_end(b: Booking) -> datetime:
    return datetime.combine(b.timeslot.date, b.timeslot.end_time)


def _fmt(b: Booking) -> str:
    """One-line booking description for messages."""
    d = b.timeslot.date
    t = b.timeslot.start_time
    return f"{b.service.name} у {b.master.name} — {d.day:02d}.{d.month:02d} о {t.hour:02d}:{t.minute:02d}"


# ─── Send helpers ─────────────────────────────────────────────────────────────

async def _safe_send(bot: Bot, telegram_id: int, text: str, **kwargs) -> bool:
    """Send message; return False if user blocked the bot or chat not found."""
    try:
        await bot.send_message(telegram_id, text, **kwargs)
        return True
    except TelegramForbiddenError:
        logger.warning("User %s has blocked the bot — skipping reminder.", telegram_id)
        return False
    except TelegramBadRequest as e:
        logger.warning("Bad request sending to %s: %s", telegram_id, e)
        return False
    except Exception as e:
        logger.error("Failed to send message to %s: %s", telegram_id, e)
        return False


# ─── 24-hour reminder ─────────────────────────────────────────────────────────

async def send_24h_reminders(bot: Bot) -> None:
    now = datetime.now()
    bookings = await _load_bookings(
        flag_column=Booking.reminder_24h_sent,
        statuses=[BookingStatus.CONFIRMED, BookingStatus.PENDING],
    )

    to_mark: list[int] = []
    for b in bookings:
        if b.timeslot is None or b.user is None:
            continue
        slot_dt = _slot_start(b)
        # Send only when within the 24h window and appointment is still in future
        time_until = slot_dt - now
        if timedelta(0) < time_until <= _24H_WINDOW:
            text = (
                "🔔 <b>Нагадування!</b>\n\n"
                f"Завтра у вас запис:\n"
                f"✂️ {b.service.name}\n"
                f"👩 Майстер: {b.master.name}\n"
                f"📅 {slot_dt.strftime('%d.%m.%Y')} о {slot_dt.strftime('%H:%M')}\n\n"
                "Підтвердіть вашу присутність:"
            )
            sent = await _safe_send(
                bot, b.user.telegram_id, text,
                reply_markup=reminder_24h_keyboard(b.id),
            )
            if sent:
                to_mark.append(b.id)

    if to_mark:
        async with async_session_factory() as session:
            for booking_id in to_mark:
                booking = await session.get(Booking, booking_id)
                if booking:
                    booking.reminder_24h_sent = True
            await session.commit()
        logger.info("Sent 24h reminders for %d bookings.", len(to_mark))


# ─── 2-hour reminder ──────────────────────────────────────────────────────────

async def send_2h_reminders(bot: Bot) -> None:
    now = datetime.now()
    bookings = await _load_bookings(
        flag_column=Booking.reminder_2h_sent,
        statuses=[BookingStatus.CONFIRMED, BookingStatus.PENDING],
    )

    to_mark: list[int] = []
    for b in bookings:
        if b.timeslot is None or b.user is None:
            continue
        slot_dt = _slot_start(b)
        time_until = slot_dt - now
        if timedelta(0) < time_until <= _2H_WINDOW:
            text = (
                "⏰ <b>Через 2 години у вас запис!</b>\n\n"
                f"✂️ {b.service.name}\n"
                f"👩 Майстер: {b.master.name}\n"
                f"🕐 {slot_dt.strftime('%H:%M')}\n\n"
                "Чекаємо вас! 💅"
            )
            sent = await _safe_send(
                bot, b.user.telegram_id, text,
                reply_markup=reminder_2h_keyboard(b.id),
            )
            if sent:
                to_mark.append(b.id)

    if to_mark:
        async with async_session_factory() as session:
            for booking_id in to_mark:
                booking = await session.get(Booking, booking_id)
                if booking:
                    booking.reminder_2h_sent = True
            await session.commit()
        logger.info("Sent 2h reminders for %d bookings.", len(to_mark))


# ─── Post-visit review request ────────────────────────────────────────────────

async def send_review_requests(bot: Bot) -> None:
    now = datetime.now()
    bookings = await _load_bookings(
        flag_column=Booking.review_sent,
        statuses=[BookingStatus.CONFIRMED],
    )

    to_mark: list[int] = []
    for b in bookings:
        if b.timeslot is None or b.user is None:
            continue
        # Send 2h after the appointment end time
        review_time = _slot_end(b) + _REVIEW_DELAY
        if review_time <= now:
            text = (
                "💅 <b>Як пройшов ваш візит?</b>\n\n"
                f"Ви відвідали: {b.service.name} у {b.master.name}\n\n"
                "Оцініть якість послуги — це допомагає нам покращувати сервіс:"
            )
            sent = await _safe_send(
                bot, b.user.telegram_id, text,
                reply_markup=review_keyboard(b.id),
            )
            if sent:
                to_mark.append(b.id)

    if to_mark:
        async with async_session_factory() as session:
            for booking_id in to_mark:
                booking = await session.get(Booking, booking_id)
                if booking:
                    booking.review_sent = True
                    booking.status = BookingStatus.COMPLETED
            await session.commit()
        logger.info("Sent review requests for %d bookings.", len(to_mark))
