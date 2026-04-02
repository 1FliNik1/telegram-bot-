from __future__ import annotations

from datetime import date, time

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.filters.admin import IsAdmin
from src.bot.keyboards.admin_kb import (
    AdminCancelCallback,
    AdminConfirmCallback,
    AdminMasterCallback,
    AdminSkipCallback,
    AdminSlotDateCallback,
    AdminSlotHourCallback,
    admin_confirm_keyboard,
    admin_hours_keyboard,
    admin_slot_dates_keyboard,
    admin_slot_masters_keyboard,
)
from src.bot.states.admin import AdminSlotState
from src.db.base import async_session_factory
from src.db.repositories.admin_repo import AdminMasterRepository, AdminSlotRepository

router = Router(name="admin_slots")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ─── Entry: "⏰ Слоти" button ──────────────────────────────────────────────────

@router.message(F.text == "⏰ Слоти")
async def admin_slots_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        masters = await repo.get_all_masters()

    if not masters:
        await message.answer("Спочатку додайте майстра.")
        return

    await state.set_state(AdminSlotState.choose_master)
    await message.answer(
        "⏰ <b>Управління слотами</b>\n\nОберіть майстра:",
        reply_markup=admin_slot_masters_keyboard(masters),
    )


# ─── Choose master ─────────────────────────────────────────────────────────────

@router.callback_query(AdminMasterCallback.filter(), StateFilter(AdminSlotState.choose_master))
async def slots_choose_date(
    callback: CallbackQuery, callback_data: AdminMasterCallback, state: FSMContext
) -> None:
    async with async_session_factory() as session:
        repo = AdminMasterRepository(session)
        master = await repo.get(callback_data.master_id)

    if master is None:
        await callback.answer("Майстра не знайдено.", show_alert=True)
        return

    await state.update_data(master_id=master.id, master_name=master.name)
    await state.set_state(AdminSlotState.choose_date)

    await callback.message.edit_text(
        f"👤 <b>{master.name}</b>\n\n📅 Оберіть дату для додавання слотів:",
        reply_markup=admin_slot_dates_keyboard(master.id),
    )
    await callback.answer()


# ─── Choose date → choose hours ────────────────────────────────────────────────

@router.callback_query(AdminSlotDateCallback.filter(), StateFilter(AdminSlotState.choose_date))
async def slots_choose_hours(
    callback: CallbackQuery, callback_data: AdminSlotDateCallback, state: FSMContext
) -> None:
    chosen_date = date.fromisoformat(callback_data.date_str)
    await state.update_data(chosen_date=callback_data.date_str, selected_hours=[])
    await state.set_state(AdminSlotState.choose_hours)

    date_str = f"{chosen_date.day:02d}.{chosen_date.month:02d}.{chosen_date.year}"
    await callback.message.edit_text(
        f"📅 <b>{date_str}</b>\n\n"
        "Оберіть <b>робочі години</b> (натисніть кілька раз для вибору, потім ✅ Зберегти):",
        reply_markup=admin_hours_keyboard(set()),
    )
    await callback.answer()


# ─── Toggle hour selection ─────────────────────────────────────────────────────

@router.callback_query(AdminSlotHourCallback.filter(), StateFilter(AdminSlotState.choose_hours))
async def slots_toggle_hour(
    callback: CallbackQuery, callback_data: AdminSlotHourCallback, state: FSMContext
) -> None:
    data = await state.get_data()
    selected: list[int] = data.get("selected_hours", [])

    if callback_data.hour in selected:
        selected.remove(callback_data.hour)
    else:
        selected.append(callback_data.hour)

    await state.update_data(selected_hours=selected)
    await callback.message.edit_reply_markup(
        reply_markup=admin_hours_keyboard(set(selected))
    )
    await callback.answer()


# ─── Confirm — generate slots ──────────────────────────────────────────────────

@router.callback_query(AdminConfirmCallback.filter(), StateFilter(AdminSlotState.choose_hours))
async def slots_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected_hours: list[int] = sorted(data.get("selected_hours", []))
    master_name: str = data["master_name"]
    chosen_date = date.fromisoformat(data["chosen_date"])

    if not selected_hours:
        await callback.answer("Оберіть хоча б одну годину.", show_alert=True)
        return

    # Show confirm summary before writing
    hours_text = ", ".join(f"{h:02d}:00" for h in selected_hours)
    date_str = f"{chosen_date.day:02d}.{chosen_date.month:02d}.{chosen_date.year}"
    await state.set_state(AdminSlotState.confirm)
    await callback.message.edit_text(
        f"📋 <b>Підтвердіть додавання слотів:</b>\n\n"
        f"👤 {master_name}\n"
        f"📅 {date_str}\n"
        f"🕐 Години: {hours_text}\n\n"
        f"Буде додано {len(selected_hours)} слотів по 60 хв.",
        reply_markup=admin_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminConfirmCallback.filter(), StateFilter(AdminSlotState.confirm))
async def slots_save(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected_hours: list[int] = sorted(data.get("selected_hours", []))
    master_id: int = data["master_id"]
    chosen_date = date.fromisoformat(data["chosen_date"])

    total_added = 0
    async with async_session_factory() as session:
        repo = AdminSlotRepository(session)
        for h in selected_hours:
            added = await repo.create_slots_for_day(
                master_id=master_id,
                target_date=chosen_date,
                work_start=time(h, 0),
                work_end=time(h + 1, 0),
                slot_duration_minutes=60,
            )
            total_added += added
        await session.commit()

    await state.clear()
    await callback.answer(f"✅ Додано {total_added} слотів.")

    date_str = f"{chosen_date.day:02d}.{chosen_date.month:02d}.{chosen_date.year}"
    await callback.message.edit_text(
        f"✅ Додано <b>{total_added}</b> слотів для {data['master_name']} на {date_str}.\n\n"
        "Натисніть ⏰ Слоти щоб продовжити."
    )


# ─── Delete slots for a day ────────────────────────────────────────────────────

@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminSlotState.choose_hours))
async def slots_delete_day(callback: CallbackQuery, state: FSMContext) -> None:
    """Pressing 'Skip' in hours selection = remove all available slots for that day."""
    data = await state.get_data()
    master_id: int = data["master_id"]
    chosen_date = date.fromisoformat(data["chosen_date"])

    async with async_session_factory() as session:
        repo = AdminSlotRepository(session)
        removed = await repo.delete_day_slots(master_id, chosen_date)
        await session.commit()

    await state.clear()
    date_str = f"{chosen_date.day:02d}.{chosen_date.month:02d}.{chosen_date.year}"
    await callback.answer(f"🗑 Видалено {removed} слотів.")
    await callback.message.edit_text(
        f"🗑 Видалено <b>{removed}</b> вільних слотів для {data['master_name']} на {date_str}."
    )


# ─── Cancel ────────────────────────────────────────────────────────────────────

@router.callback_query(AdminCancelCallback.filter(), StateFilter(AdminSlotState))
async def cancel_slots_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Скасовано.")
    await callback.answer()
