from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.booking_kb import (
    BookBackToCatsCallback,
    BookCancelFlowCallback,
    BookCategoryCallback,
    BookConfirmCallback,
    BookServiceCallback,
    BookStartCallback,
    DateSelectCallback,
    MasterSelectCallback,
    SlotSelectCallback,
    booking_categories_keyboard,
    booking_services_keyboard,
    confirm_keyboard,
    dates_keyboard,
    format_date_long,
    format_time,
    masters_keyboard,
    timeslots_keyboard,
)
from src.bot.states.booking import BookingState
from src.db.base import async_session_factory
from src.db.repositories.master_repo import MasterRepository
from src.db.repositories.service_repo import (
    ServiceCategoryRepository,
    ServiceRepository,
)
from src.db.repositories.timeslot_repo import TimeSlotRepository
from src.services import booking_service
from src.services.booking_service import SlotAlreadyTaken

router = Router(name="booking")

# ─── Helpers ─────────────────────────────────────────────────────────────────

NO_MASTERS_TEXT = (
    "😔 Наразі немає доступних майстрів для цієї послуги.\n"
    "Спробуйте обрати іншу послугу або зверніться до адміністратора."
)
NO_DATES_TEXT = (
    "📅 Немає вільних дат у найближчі 14 днів.\n"
    "Спробуйте пізніше або оберіть іншого майстра."
)
NO_SLOTS_TEXT = (
    "😕 На цю дату всі слоти зайняті.\n"
    "Оберіть іншу дату."
)
CANCELLED_TEXT = "❌ Запис скасовано. Натисніть ✂️ Записатись щоб почати знову."


async def _get_master_ids_for_service(service_id: int) -> list[int]:
    async with async_session_factory() as session:
        repo = MasterRepository(session)
        masters = await repo.get_masters_by_service(service_id)
    return [m.id for m in masters]


def _service_price_str(service) -> str:
    if service.price_max:
        return f"від {int(service.price)}–{int(service.price_max)} грн"
    return f"{int(service.price)} грн"


# ─── Entry point: "✂️ Записатись" button or /book ────────────────────────────

@router.message(Command("book"))
@router.message(F.text == "📅 Записатись")
async def cmd_book(message: Message, state: FSMContext) -> None:
    await state.clear()

    async with async_session_factory() as session:
        repo = ServiceCategoryRepository(session)
        categories = await repo.get_active_categories()

    if not categories:
        await message.answer("На жаль, каталог послуг порожній. Спробуйте пізніше.")
        return

    await state.set_state(BookingState.select_service)
    await message.answer(
        "✂️ <b>Записатись на послугу</b>\n\nВиберіть категорію:",
        reply_markup=booking_categories_keyboard(categories),
    )


# ─── Entry from catalog service detail ───────────────────────────────────────

@router.callback_query(BookStartCallback.filter())
async def on_catalog_book_start(
    callback: CallbackQuery,
    callback_data: BookStartCallback,
    state: FSMContext,
) -> None:
    await state.clear()

    async with async_session_factory() as session:
        svc_repo = ServiceRepository(session)
        service = await svc_repo.get_service_by_id(callback_data.service_id)
        if service is None:
            await callback.answer("Послугу не знайдено.", show_alert=True)
            return

        master_repo = MasterRepository(session)
        masters = await master_repo.get_masters_by_service(service.id)

    if not masters:
        await callback.answer(NO_MASTERS_TEXT, show_alert=True)
        return

    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        service_duration=service.duration_minutes,
        service_price=_service_price_str(service),
    )
    await state.set_state(BookingState.select_master)

    await callback.message.answer(
        f"✂️ <b>{service.name}</b>\n\nВиберіть майстра:",
        reply_markup=masters_keyboard(masters),
    )
    await callback.answer()


# ─── select_service: category clicked ────────────────────────────────────────

@router.callback_query(BookCategoryCallback.filter(), StateFilter(BookingState.select_service))
async def on_book_category(
    callback: CallbackQuery,
    callback_data: BookCategoryCallback,
    state: FSMContext,
) -> None:
    async with async_session_factory() as session:
        cat_repo = ServiceCategoryRepository(session)
        category = await cat_repo.get(callback_data.category_id)
        if category is None:
            await callback.answer("Категорію не знайдено.", show_alert=True)
            return

        svc_repo = ServiceRepository(session)
        services = await svc_repo.get_services_by_category(callback_data.category_id)

    if not services:
        await callback.answer("У цій категорії поки немає послуг.", show_alert=True)
        return

    await state.update_data(category_id=callback_data.category_id)
    cat_label = f"{category.emoji} {category.name}" if category.emoji else category.name
    await callback.message.edit_text(
        f"<b>{cat_label}</b>\n\nВиберіть послугу:",
        reply_markup=booking_services_keyboard(services),
    )
    await callback.answer()


# ─── select_service: back to categories ──────────────────────────────────────

@router.callback_query(BookBackToCatsCallback.filter(), StateFilter(BookingState.select_service))
async def on_book_back_to_cats(callback: CallbackQuery, state: FSMContext) -> None:
    async with async_session_factory() as session:
        repo = ServiceCategoryRepository(session)
        categories = await repo.get_active_categories()

    await callback.message.edit_text(
        "✂️ <b>Записатись на послугу</b>\n\nВиберіть категорію:",
        reply_markup=booking_categories_keyboard(categories),
    )
    await callback.answer()


# ─── select_service: service clicked → go to select_master ───────────────────

@router.callback_query(BookServiceCallback.filter(), StateFilter(BookingState.select_service))
async def on_book_service(
    callback: CallbackQuery,
    callback_data: BookServiceCallback,
    state: FSMContext,
) -> None:
    async with async_session_factory() as session:
        svc_repo = ServiceRepository(session)
        service = await svc_repo.get_service_by_id(callback_data.service_id)
        if service is None:
            await callback.answer("Послугу не знайдено.", show_alert=True)
            return

        master_repo = MasterRepository(session)
        masters = await master_repo.get_masters_by_service(service.id)

    if not masters:
        await callback.answer(NO_MASTERS_TEXT, show_alert=True)
        return

    await state.update_data(
        service_id=service.id,
        service_name=service.name,
        service_duration=service.duration_minutes,
        service_price=_service_price_str(service),
    )
    await state.set_state(BookingState.select_master)

    await callback.message.edit_text(
        f"✂️ <b>{service.name}</b>\n\nВиберіть майстра:",
        reply_markup=masters_keyboard(masters),
    )
    await callback.answer()


# ─── select_master → select_date ─────────────────────────────────────────────

@router.callback_query(MasterSelectCallback.filter(), StateFilter(BookingState.select_master))
async def on_book_master(
    callback: CallbackQuery,
    callback_data: MasterSelectCallback,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    service_id: int = data["service_id"]
    service_duration: int = data["service_duration"]

    # 0 means "any available master"
    if callback_data.master_id == 0:
        master_ids = await _get_master_ids_for_service(service_id)
        master_name = "Будь-який вільний"
        chosen_master_id = None
    else:
        master_ids = [callback_data.master_id]
        chosen_master_id = callback_data.master_id
        async with async_session_factory() as session:
            repo = MasterRepository(session)
            master = await repo.get(callback_data.master_id)
        master_name = master.name if master else "Майстер"

    async with async_session_factory() as session:
        slot_repo = TimeSlotRepository(session)
        available_dates = await slot_repo.get_available_dates(master_ids, service_duration)

    if not available_dates:
        await callback.answer(NO_DATES_TEXT, show_alert=True)
        return

    await state.update_data(
        chosen_master_id=chosen_master_id,
        master_name=master_name,
        master_ids=master_ids,
    )
    await state.set_state(BookingState.select_date)

    await callback.message.edit_text(
        f"👤 Майстер: <b>{master_name}</b>\n\n📅 Оберіть дату:",
        reply_markup=dates_keyboard(available_dates),
    )
    await callback.answer()


# ─── select_date → select_time ───────────────────────────────────────────────

@router.callback_query(DateSelectCallback.filter(), StateFilter(BookingState.select_date))
async def on_book_date(
    callback: CallbackQuery,
    callback_data: DateSelectCallback,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    master_ids: list[int] = data["master_ids"]
    service_duration: int = data["service_duration"]

    chosen_date = date.fromisoformat(callback_data.date_str)

    async with async_session_factory() as session:
        slot_repo = TimeSlotRepository(session)
        slots = await slot_repo.get_available_slots(master_ids, chosen_date)

    # filter by duration
    valid_slots = [
        s for s in slots
        if (s.end_time.hour * 60 + s.end_time.minute) -
           (s.start_time.hour * 60 + s.start_time.minute) >= service_duration
    ]

    if not valid_slots:
        await callback.answer(NO_SLOTS_TEXT, show_alert=True)
        return

    await state.update_data(chosen_date=callback_data.date_str)
    await state.set_state(BookingState.select_time)

    date_label = format_date_long(chosen_date)
    await callback.message.edit_text(
        f"📅 <b>{date_label}</b>\n\n🕐 Оберіть час:",
        reply_markup=timeslots_keyboard(slots, service_duration),
    )
    await callback.answer()


# ─── select_time → confirm ────────────────────────────────────────────────────

@router.callback_query(SlotSelectCallback.filter(), StateFilter(BookingState.select_time))
async def on_book_slot(
    callback: CallbackQuery,
    callback_data: SlotSelectCallback,
    state: FSMContext,
) -> None:
    async with async_session_factory() as session:
        slot_repo = TimeSlotRepository(session)
        slot = await slot_repo.get(callback_data.timeslot_id)
        if slot is None or not slot.is_available:
            await callback.answer(
                "Цей час щойно зайняли! Оберіть інший.", show_alert=True
            )
            return

        # Get the actual master for this slot
        master_repo = MasterRepository(session)
        master = await master_repo.get(slot.master_id)

    data = await state.get_data()
    actual_master_name = master.name if master else "Майстер"

    await state.update_data(
        timeslot_id=slot.id,
        actual_master_id=slot.master_id,
        actual_master_name=actual_master_name,
        start_time_str=format_time(slot.start_time),
        end_time_str=format_time(slot.end_time),
    )
    await state.set_state(BookingState.confirm)

    chosen_date = date.fromisoformat(data["chosen_date"])
    date_label = format_date_long(chosen_date)

    summary = (
        "📋 <b>Підтвердіть запис:</b>\n\n"
        f"✂️ {data['service_name']}\n"
        f"👩 Майстер: {actual_master_name}\n"
        f"📅 {date_label}\n"
        f"🕐 {format_time(slot.start_time)} — {format_time(slot.end_time)}\n"
        f"💰 {data['service_price']}"
    )
    await callback.message.edit_text(summary, reply_markup=confirm_keyboard())
    await callback.answer()


# ─── confirm → done ───────────────────────────────────────────────────────────

@router.callback_query(BookConfirmCallback.filter(), StateFilter(BookingState.confirm))
async def on_book_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    try:
        await booking_service.confirm_booking(callback.from_user, data)
    except SlotAlreadyTaken:
        await callback.answer(
            "⚠️ Цей час щойно зайняли!\n"
            "Поверніться до вибору дати та оберіть інший слот.",
            show_alert=True,
        )
        # Rewind to date selection so user can pick another slot
        await state.set_state(BookingState.select_date)
        return

    await state.clear()

    chosen_date = date.fromisoformat(data["chosen_date"])
    date_label = format_date_long(chosen_date)

    success_text = (
        "✅ <b>Записано!</b>\n\n"
        f"✂️ {data['service_name']}\n"
        f"👩 {data['actual_master_name']}\n"
        f"📅 {date_label}\n"
        f"🕐 {data['start_time_str']} — {data['end_time_str']}\n\n"
        "Нагадаємо вам за день та за 2 години.\n"
        "Щоб переглянути або скасувати — натисніть 📅 Мої записи"
    )
    await callback.message.edit_text(success_text)
    await callback.answer("✅ Запис підтверджено!")


# ─── Cancel from any booking state ───────────────────────────────────────────

@router.callback_query(BookCancelFlowCallback.filter(), StateFilter(BookingState))
async def on_book_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(CANCELLED_TEXT)
    await callback.answer()
