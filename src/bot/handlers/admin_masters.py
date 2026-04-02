from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.filters.admin import IsAdmin
from src.bot.keyboards.admin_kb import (
    AdminActionCallback,
    AdminCancelCallback,
    AdminConfirmCallback,
    AdminMasterCallback,
    AdminMasterToggleCallback,
    AdminSkipCallback,
    admin_confirm_keyboard,
    admin_master_detail_keyboard,
    admin_masters_keyboard,
    admin_skip_keyboard,
)
from src.bot.states.admin import AdminMasterState
from src.db.base import async_session_factory
from src.db.repositories.admin_repo import AdminBookingRepository, AdminMasterRepository

router = Router(name="admin_masters")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _master_summary(data: dict) -> str:
    spec = data.get("specialization") or "—"
    bio = data.get("bio") or "—"
    photo = "є" if data.get("photo_file_id") else "немає"
    return (
        f"<b>{data['name']}</b>\n"
        f"Спеціалізація: {spec}\n"
        f"Біо: {bio}\n"
        f"Фото: {photo}"
    )


# ─── Masters list ──────────────────────────────────────────────────────────────

@router.message(F.text == "👤 Майстри")
@router.callback_query(AdminActionCallback.filter(F.action == "masters"))
async def show_masters(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        masters = await repo.get_all_masters()

    text = "👤 <b>Майстри</b>\n\nНатисніть для деталей або додайте нового:"
    kb = admin_masters_keyboard(masters)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


# ─── Master detail ─────────────────────────────────────────────────────────────

@router.callback_query(AdminMasterCallback.filter())
async def master_detail(callback: CallbackQuery, callback_data: AdminMasterCallback) -> None:
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        master = await repo.get(callback_data.master_id)
        if master is None:
            await callback.answer("Майстра не знайдено.", show_alert=True)
            return

        booking_repo = AdminBookingRepository(session)
        bookings = await booking_repo.get_bookings_by_master(master.id)

    spec = master.specialization or "—"
    status = "✅ Активний" if master.is_active else "❌ Неактивний"
    upcoming = len(bookings)
    text = (
        f"<b>{master.name}</b>\n"
        f"Спеціалізація: {spec}\n"
        f"Статус: {status}\n"
        f"Майбутніх записів: {upcoming}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_master_detail_keyboard(master.id, master.is_active),
    )
    await callback.answer()


# ─── Bookings by master ────────────────────────────────────────────────────────

@router.callback_query(AdminActionCallback.filter(F.action.startswith("slots_master_")))
async def master_bookings(callback: CallbackQuery, callback_data: AdminActionCallback) -> None:
    master_id = int(callback_data.action.split("_")[-1])
    async with async_session_factory() as session:
        m_repo = AdminMasterRepository(session)
        master = await m_repo.get(master_id)
        b_repo = AdminBookingRepository(session)
        bookings = await b_repo.get_bookings_by_master(master_id)

    if not bookings:
        text = f"👩 <b>{master.name if master else '?'}</b>\n\n📭 Майбутніх записів немає."
    else:
        lines = [f"👩 <b>{master.name if master else '?'} — записи:</b>\n"]
        for b in bookings:
            t = b.timeslot
            date_str = f"{t.date.day:02d}.{t.date.month:02d}"
            time_str = f"{t.start_time.hour:02d}:{t.start_time.minute:02d}"
            client = b.user.first_name if b.user else "?"
            lines.append(f"📅 {date_str} {time_str} — {b.service.name} ({client})")
        text = "\n".join(lines)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад", callback_data=AdminMasterCallback(master_id=master_id))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(AdminMasterToggleCallback.filter())
async def toggle_master(
    callback: CallbackQuery, callback_data: AdminMasterToggleCallback
) -> None:
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        new_state = await repo.toggle_active(callback_data.master_id)
        await session.commit()

    label = "активований ✅" if new_state else "деактивований ❌"
    await callback.answer(f"Майстра {label}.")

    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        masters = await repo.get_all_masters()
    await callback.message.edit_text(
        "👤 <b>Майстри</b>:",
        reply_markup=admin_masters_keyboard(masters),
    )


# ─── Add master FSM ────────────────────────────────────────────────────────────

@router.callback_query(AdminActionCallback.filter(F.action == "add_master"))
async def add_master_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminMasterState.enter_name)
    await callback.message.edit_text("➕ <b>Новий майстер</b>\n\nВведіть <b>ім'я</b>:")
    await callback.answer()


@router.message(StateFilter(AdminMasterState.enter_name))
async def add_master_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminMasterState.enter_specialization)
    await message.answer(
        "Введіть <b>спеціалізацію</b> (наприклад: Манікюр, педикюр) або пропустіть:",
        reply_markup=admin_skip_keyboard(),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminMasterState.enter_specialization))
async def add_master_spec_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(specialization=None)
    await state.set_state(AdminMasterState.enter_bio)
    await callback.message.edit_text(
        "Введіть <b>короткий опис</b> або пропустіть:",
        reply_markup=admin_skip_keyboard(),
    )
    await callback.answer()


@router.message(StateFilter(AdminMasterState.enter_specialization))
async def add_master_specialization(message: Message, state: FSMContext) -> None:
    await state.update_data(specialization=message.text.strip())
    await state.set_state(AdminMasterState.enter_bio)
    await message.answer(
        "Введіть <b>короткий опис</b> або пропустіть:",
        reply_markup=admin_skip_keyboard(),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminMasterState.enter_bio))
async def add_master_bio_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(bio=None)
    await state.set_state(AdminMasterState.upload_photo)
    await callback.message.edit_text(
        "Надішліть <b>фото</b> майстра або пропустіть:",
        reply_markup=admin_skip_keyboard("⏩ Без фото"),
    )
    await callback.answer()


@router.message(StateFilter(AdminMasterState.enter_bio))
async def add_master_bio(message: Message, state: FSMContext) -> None:
    await state.update_data(bio=message.text.strip())
    await state.set_state(AdminMasterState.upload_photo)
    await message.answer(
        "Надішліть <b>фото</b> майстра або пропустіть:",
        reply_markup=admin_skip_keyboard("⏩ Без фото"),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminMasterState.upload_photo))
async def add_master_photo_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    await _show_master_confirm(callback.message, state, edit=True)
    await callback.answer()


@router.message(F.photo, StateFilter(AdminMasterState.upload_photo))
async def add_master_photo(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await _show_master_confirm(message, state)


async def _show_master_confirm(message: Message, state: FSMContext, edit: bool = False) -> None:
    data = await state.get_data()
    text = "📋 <b>Перевірте дані:</b>\n\n" + _master_summary(data)
    await state.set_state(AdminMasterState.confirm)
    if edit:
        await message.edit_text(text, reply_markup=admin_confirm_keyboard())
    else:
        await message.answer(text, reply_markup=admin_confirm_keyboard())


@router.callback_query(AdminConfirmCallback.filter(), StateFilter(AdminMasterState.confirm))
async def add_master_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        await repo.create_master(
            name=data["name"],
            specialization=data.get("specialization"),
            bio=data.get("bio"),
            photo_file_id=data.get("photo_file_id"),
        )
        await session.commit()
        masters = await repo.get_all_masters()

    await state.clear()
    await callback.answer("✅ Майстра додано!")
    await callback.message.edit_text(
        "✅ Майстра додано!\n\n👤 <b>Майстри</b>:",
        reply_markup=admin_masters_keyboard(masters),
    )


# ─── Cancel any master state ───────────────────────────────────────────────────

@router.callback_query(AdminCancelCallback.filter(), StateFilter(AdminMasterState))
async def cancel_master_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        masters = await repo.get_all_masters()
    await callback.message.edit_text(
        "👤 <b>Майстри</b>:",
        reply_markup=admin_masters_keyboard(masters),
    )
    await callback.answer()
