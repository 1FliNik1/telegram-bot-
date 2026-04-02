from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.booking_kb import (
    dates_keyboard,
    format_date_long,
    format_time,
)
from src.bot.keyboards.my_bookings_kb import (
    AbortCancelCallback,
    CancelBookingCallback,
    ConfirmCancelCallback,
    RepeatBookingCallback,
    bookings_keyboard,
    can_cancel,
    confirm_cancel_keyboard,
    format_booking_line,
    is_future,
    no_bookings_keyboard,
)
from src.bot.states.booking import BookingState
from src.db.base import async_session_factory
from src.db.models.booking import Booking
from src.db.repositories.booking_repo import BookingRepository
from src.db.repositories.master_repo import MasterRepository
from src.db.repositories.service_repo import ServiceRepository
from src.db.repositories.timeslot_repo import TimeSlotRepository
from src.db.repositories.user_repo import UserRepository

router = Router(name="my_bookings")

NO_BOOKINGS_TEXT = (
    "📭 У вас поки немає активних записів.\n\n"
    "Натисніть ✂️ Записатись щоб забронювати послугу."
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _service_price_str(service) -> str:
    if service.price_max:
        return f"від {int(service.price)}–{int(service.price_max)} грн"
    return f"{int(service.price)} грн"


async def _fetch_user_bookings(telegram_id: int) -> list[Booking]:
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if user is None:
            return []
        booking_repo = BookingRepository(session)
        all_bookings = await booking_repo.get_user_upcoming_bookings(user.id)

    # Keep only future bookings
    return [b for b in all_bookings if b.timeslot is not None and is_future(b)]


def _build_bookings_text(bookings: list[Booking]) -> str:
    lines = ["📅 <b>Ваші записи:</b>\n"]
    for i, b in enumerate(bookings):
        lines.append(format_booking_line(b, i))
        if not can_cancel(b):
            lines.append("   ⚠️ Скасування недоступне (менше 2 годин)")
        lines.append("")
    return "\n".join(lines).strip()


# ─── /my_bookings — show list ────────────────────────────────────────────────

@router.message(Command("my_bookings"))
@router.message(F.text == "📖 Мої записи")
async def cmd_my_bookings(message: Message) -> None:
    bookings = await _fetch_user_bookings(message.from_user.id)

    if not bookings:
        await message.answer(NO_BOOKINGS_TEXT, reply_markup=no_bookings_keyboard())
        return

    await message.answer(
        _build_bookings_text(bookings),
        reply_markup=bookings_keyboard(bookings),
    )


# ─── "Записатись" from empty state ────────────────────────────────────────────

@router.callback_query(F.data == "book_from_empty")
async def on_book_from_empty(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped 'Записатись' from the empty bookings screen."""
    await callback.message.delete()
    await callback.answer()
    # Trigger the booking flow naturally via fake text — just send a hint
    await callback.message.answer(
        "Натисніть кнопку ✂️ <b>Записатись</b> у головному меню."
    )


# ─── Cancel flow ─────────────────────────────────────────────────────────────

@router.callback_query(CancelBookingCallback.filter())
async def on_cancel_booking(
    callback: CallbackQuery, callback_data: CancelBookingCallback
) -> None:
    """Show cancel confirmation for a specific booking."""
    booking_id = callback_data.booking_id

    # Re-fetch to make sure it's still active and still cancellable
    bookings = await _fetch_user_bookings(callback.from_user.id)
    booking = next((b for b in bookings if b.id == booking_id), None)

    if booking is None:
        await callback.answer("Запис не знайдено або вже скасовано.", show_alert=True)
        return

    if not can_cancel(booking):
        await callback.answer(
            "⚠️ Скасування неможливе — до запису менше 2 годин.",
            show_alert=True,
        )
        return

    date_label = format_date_long(booking.timeslot.date)
    time_label = f"{format_time(booking.timeslot.start_time)}–{format_time(booking.timeslot.end_time)}"

    text = (
        "❓ <b>Підтвердіть скасування:</b>\n\n"
        f"✂️ {booking.service.name}\n"
        f"👩 {booking.master.name}\n"
        f"📅 {date_label}  🕐 {time_label}\n\n"
        "Ви впевнені?"
    )
    await callback.message.edit_text(text, reply_markup=confirm_cancel_keyboard(booking_id))
    await callback.answer()


@router.callback_query(ConfirmCancelCallback.filter())
async def on_confirm_cancel(
    callback: CallbackQuery, callback_data: ConfirmCancelCallback
) -> None:
    """Actually cancel the booking."""
    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if user is None:
            await callback.answer("Користувача не знайдено.", show_alert=True)
            return

        booking_repo = BookingRepository(session)
        success = await booking_repo.cancel_booking(callback_data.booking_id, user.id)
        await session.commit()

    if not success:
        await callback.answer("Запис вже скасовано або не знайдено.", show_alert=True)
        return

    await callback.answer("✅ Запис скасовано.")

    # Re-fetch and show updated list
    bookings = await _fetch_user_bookings(callback.from_user.id)
    if not bookings:
        await callback.message.edit_text(NO_BOOKINGS_TEXT, reply_markup=no_bookings_keyboard())
    else:
        await callback.message.edit_text(
            _build_bookings_text(bookings),
            reply_markup=bookings_keyboard(bookings),
        )


@router.callback_query(AbortCancelCallback.filter())
async def on_abort_cancel(callback: CallbackQuery) -> None:
    """Go back to bookings list without cancelling."""
    bookings = await _fetch_user_bookings(callback.from_user.id)

    if not bookings:
        await callback.message.edit_text(NO_BOOKINGS_TEXT, reply_markup=no_bookings_keyboard())
    else:
        await callback.message.edit_text(
            _build_bookings_text(bookings),
            reply_markup=bookings_keyboard(bookings),
        )
    await callback.answer()


# ─── Repeat booking ───────────────────────────────────────────────────────────

@router.callback_query(RepeatBookingCallback.filter())
async def on_repeat_booking(
    callback: CallbackQuery,
    callback_data: RepeatBookingCallback,
    state: FSMContext,
) -> None:
    """Start booking FSM pre-filled with service + master, jump to date selection."""
    await state.clear()

    async with async_session_factory() as session:
        svc_repo = ServiceRepository(session)
        service = await svc_repo.get_service_by_id(callback_data.service_id)
        if service is None:
            await callback.answer("Послугу більше не доступна.", show_alert=True)
            return

        master_repo = MasterRepository(session)
        master = await master_repo.get(callback_data.master_id)

        # Check master still does this service
        masters_for_service = await master_repo.get_masters_by_service(service.id)
        master_ids = [m.id for m in masters_for_service]

    if not master_ids:
        await callback.answer("Для цієї послуги немає доступних майстрів.", show_alert=True)
        return

    # If the original master is still available — use them; otherwise "any"
    if master and master.is_active and master.id in master_ids:
        chosen_master_id = master.id
        master_name = master.name
        chosen_master_ids = [master.id]
    else:
        chosen_master_id = None
        master_name = "Будь-який вільний"
        chosen_master_ids = master_ids

    async with async_session_factory() as session:
        slot_repo = TimeSlotRepository(session)
        available_dates = await slot_repo.get_available_dates(
            chosen_master_ids, service.duration_minutes
        )

    if not available_dates:
        await callback.answer(
            "Немає вільних дат у найближчі 14 днів. Спробуйте пізніше.",
            show_alert=True,
        )
        return

    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        service_duration=service.duration_minutes,
        service_price=_service_price_str(service),
        chosen_master_id=chosen_master_id,
        master_name=master_name,
        master_ids=chosen_master_ids,
    )
    await state.set_state(BookingState.select_date)

    await callback.message.edit_text(
        f"🔄 <b>Повторний запис</b>\n\n"
        f"✂️ {service.name}\n"
        f"👩 Майстер: {master_name}\n\n"
        f"📅 Оберіть дату:",
        reply_markup=dates_keyboard(available_dates),
    )
    await callback.answer()
