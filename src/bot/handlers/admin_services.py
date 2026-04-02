from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.filters.admin import IsAdmin
from src.bot.keyboards.admin_kb import (
    AdminActionCallback,
    AdminCancelCallback,
    AdminCategoryCallback,
    AdminConfirmCallback,
    AdminServiceCallback,
    AdminServiceToggleCallback,
    AdminSkipCallback,
    admin_categories_keyboard,
    admin_confirm_keyboard,
    admin_service_detail_keyboard,
    admin_services_keyboard,
    admin_skip_keyboard,
)
from src.bot.states.admin import AdminServiceState
from src.db.base import async_session_factory
from src.db.repositories.admin_repo import AdminServiceRepository

router = Router(name="admin_services")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _svc_summary(data: dict) -> str:
    price_str = f"{data['price']} грн"
    if data.get("price_max"):
        price_str = f"від {data['price']} до {data['price_max']} грн"
    desc = data.get("description") or "—"
    photo = "є" if data.get("photo_file_id") else "немає"
    return (
        f"<b>{data['name']}</b>\n"
        f"Категорія: {data['category_name']}\n"
        f"Ціна: {price_str}\n"
        f"Тривалість: {data['duration']} хв\n"
        f"Опис: {desc}\n"
        f"Фото: {photo}"
    )


# ─── Services list ─────────────────────────────────────────────────────────────

@router.message(F.text == "🛠 Послуги")
@router.callback_query(AdminActionCallback.filter(F.action == "services"))
async def show_services(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        services = await repo.get_all_services_with_categories()

    text = "🛠 <b>Послуги</b>\n\nНатисніть для деталей або додайте нову:"
    kb = admin_services_keyboard(services)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb)


# ─── Service detail + toggle active ──────────────────────────────────────────

@router.callback_query(AdminServiceCallback.filter())
async def service_detail(callback: CallbackQuery, callback_data: AdminServiceCallback) -> None:
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        svc = await repo.get(callback_data.service_id)
        if svc is None:
            await callback.answer("Послугу не знайдено.", show_alert=True)
            return
        from src.db.models.service import ServiceCategory
        cat = await session.get(ServiceCategory, svc.category_id)
        cat_name = cat.name if cat else "?"

    price_str = f"{int(svc.price)} грн"
    if svc.price_max:
        price_str = f"від {int(svc.price)} до {int(svc.price_max)} грн"
    status = "✅ Активна" if svc.is_active else "❌ Неактивна"
    text = (
        f"<b>{svc.name}</b>\n"
        f"Категорія: {cat_name}\n"
        f"Ціна: {price_str}\n"
        f"Тривалість: {svc.duration_minutes} хв\n"
        f"Статус: {status}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_service_detail_keyboard(svc.id, svc.is_active)
    )
    await callback.answer()


@router.callback_query(AdminServiceToggleCallback.filter())
async def toggle_service(
    callback: CallbackQuery, callback_data: AdminServiceToggleCallback
) -> None:
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        new_state = await repo.toggle_active(callback_data.service_id)
        await session.commit()

    label = "активована ✅" if new_state else "деактивована ❌"
    await callback.answer(f"Послугу {label}.")

    # Refresh services list
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        services = await repo.get_all_services_with_categories()
    await callback.message.edit_text(
        "🛠 <b>Послуги</b>\n\nНатисніть для деталей або додайте нову:",
        reply_markup=admin_services_keyboard(services),
    )


# ─── Add service FSM ──────────────────────────────────────────────────────────

@router.callback_query(AdminActionCallback.filter(F.action == "add_service"))
async def add_service_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        categories = await repo.get_all_categories()

    if not categories:
        await callback.answer("Спочатку додайте категорію.", show_alert=True)
        return

    await state.set_state(AdminServiceState.choose_category)
    await callback.message.edit_text(
        "➕ <b>Нова послуга</b>\n\nОберіть категорію:",
        reply_markup=admin_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(AdminCategoryCallback.filter(), StateFilter(AdminServiceState.choose_category))
async def add_service_category(
    callback: CallbackQuery, callback_data: AdminCategoryCallback, state: FSMContext
) -> None:
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        cats = await repo.get_all_categories()
    cat = next((c for c in cats if c.id == callback_data.category_id), None)
    await state.update_data(category_id=callback_data.category_id, category_name=cat.name if cat else "?")
    await state.set_state(AdminServiceState.enter_name)
    await callback.message.edit_text("Введіть <b>назву</b> послуги:")
    await callback.answer()


@router.message(StateFilter(AdminServiceState.enter_name))
async def add_service_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminServiceState.enter_price)
    await message.answer("Введіть <b>ціну</b> (грн, тільки число):")


@router.message(StateFilter(AdminServiceState.enter_price))
async def add_service_price(message: Message, state: FSMContext) -> None:
    try:
        price = Decimal(message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Невірний формат. Введіть число, наприклад: 350")
        return
    await state.update_data(price=str(price))
    await state.set_state(AdminServiceState.enter_price_max)
    await message.answer(
        "Введіть <b>максимальну ціну</b> (якщо є діапазон), або пропустіть:",
        reply_markup=admin_skip_keyboard("⏩ Без максимуму"),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminServiceState.enter_price_max))
async def add_service_price_max_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(price_max=None)
    await state.set_state(AdminServiceState.enter_duration)
    await callback.message.edit_text("Введіть <b>тривалість</b> (хвилини):")
    await callback.answer()


@router.message(StateFilter(AdminServiceState.enter_price_max))
async def add_service_price_max(message: Message, state: FSMContext) -> None:
    try:
        price_max = Decimal(message.text.strip().replace(",", "."))
        if price_max <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Невірний формат. Введіть число або натисніть «Пропустити».")
        return
    await state.update_data(price_max=str(price_max))
    await state.set_state(AdminServiceState.enter_duration)
    await message.answer("Введіть <b>тривалість</b> (хвилини):")


@router.message(StateFilter(AdminServiceState.enter_duration))
async def add_service_duration(message: Message, state: FSMContext) -> None:
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введіть ціле число хвилин, наприклад: 60")
        return
    await state.update_data(duration=duration)
    await state.set_state(AdminServiceState.enter_description)
    await message.answer(
        "Введіть <b>опис</b> послуги (або пропустіть):",
        reply_markup=admin_skip_keyboard(),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminServiceState.enter_description))
async def add_service_desc_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(AdminServiceState.upload_photo)
    await callback.message.edit_text(
        "Надішліть <b>фото</b> послуги або пропустіть:",
        reply_markup=admin_skip_keyboard("⏩ Без фото"),
    )
    await callback.answer()


@router.message(StateFilter(AdminServiceState.enter_description))
async def add_service_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminServiceState.upload_photo)
    await message.answer(
        "Надішліть <b>фото</b> послуги або пропустіть:",
        reply_markup=admin_skip_keyboard("⏩ Без фото"),
    )


@router.callback_query(AdminSkipCallback.filter(), StateFilter(AdminServiceState.upload_photo))
async def add_service_photo_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    await _show_service_confirm(callback.message, state, edit=True)
    await callback.answer()


@router.message(F.photo, StateFilter(AdminServiceState.upload_photo))
async def add_service_photo(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=file_id)
    await _show_service_confirm(message, state)


async def _show_service_confirm(message: Message, state: FSMContext, edit: bool = False) -> None:
    data = await state.get_data()
    text = "📋 <b>Перевірте дані:</b>\n\n" + _svc_summary(data)
    await state.set_state(AdminServiceState.confirm)
    if edit:
        await message.edit_text(text, reply_markup=admin_confirm_keyboard())
    else:
        await message.answer(text, reply_markup=admin_confirm_keyboard())


@router.callback_query(AdminConfirmCallback.filter(), StateFilter(AdminServiceState.confirm))
async def add_service_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        await repo.create_service(
            category_id=data["category_id"],
            name=data["name"],
            price=Decimal(data["price"]),
            duration_minutes=data["duration"],
            price_max=Decimal(data["price_max"]) if data.get("price_max") else None,
            description=data.get("description"),
            photo_file_id=data.get("photo_file_id"),
        )
        await session.commit()
        services = await repo.get_all_services_with_categories()

    await state.clear()
    await callback.answer("✅ Послугу додано!")
    await callback.message.edit_text(
        "✅ Послугу додано!\n\n🛠 <b>Послуги</b>:",
        reply_markup=admin_services_keyboard(services),
    )


# ─── Cancel any service state ─────────────────────────────────────────────────

@router.callback_query(AdminCancelCallback.filter(), StateFilter(AdminServiceState))
async def cancel_service_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        repo = AdminServiceRepository(session)
        services = await repo.get_all_services_with_categories()
    await callback.message.edit_text(
        "🛠 <b>Послуги</b>:",
        reply_markup=admin_services_keyboard(services),
    )
    await callback.answer()
