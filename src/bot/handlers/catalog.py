from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.catalog_kb import (
    CatalogBackCallback,
    CategoryCallback,
    ServiceCallback,
    categories_keyboard,
    service_detail_keyboard,
    services_keyboard,
)
from src.db.base import async_session_factory
from src.db.repositories.service_repo import (
    ServiceCategoryRepository,
    ServiceRepository,
)

router = Router(name="catalog")

CATALOG_EMPTY = "На жаль, каталог послуг порожній. Спробуйте пізніше."
CATEGORY_EMPTY = "У цій категорії поки немає послуг."
SERVICE_NOT_FOUND = "Послугу не знайдено або вона більше не доступна."


# ─── /catalog або текстова кнопка "Каталог послуг" ───────────────────────────

@router.message(Command("catalog"))
@router.message(F.text == "📋 Каталог послуг")
async def show_catalog(message: Message) -> None:
    async with async_session_factory() as session:
        repo = ServiceCategoryRepository(session)
        categories = await repo.get_active_categories()

    if not categories:
        await message.answer(CATALOG_EMPTY)
        return

    await message.answer(
        "Оберіть категорію послуг:",
        reply_markup=categories_keyboard(categories),
    )


# ─── Вибір категорії → список послуг ─────────────────────────────────────────

@router.callback_query(CategoryCallback.filter())
async def show_services(callback: CallbackQuery, callback_data: CategoryCallback) -> None:
    async with async_session_factory() as session:
        cat_repo = ServiceCategoryRepository(session)
        svc_repo = ServiceRepository(session)

        category = await cat_repo.get(callback_data.category_id)
        if category is None:
            await callback.answer("Категорію не знайдено.", show_alert=True)
            return

        services = await svc_repo.get_services_by_category(callback_data.category_id)

    if not services:
        await callback.answer(CATEGORY_EMPTY, show_alert=True)
        return

    cat_label = f"{category.emoji} {category.name}" if category.emoji else category.name
    await callback.message.edit_text(
        f"<b>{cat_label}</b>\n\nОберіть послугу:",
        reply_markup=services_keyboard(services),
    )
    await callback.answer()


# ─── Кнопка "← Назад" → повернення до категорій ──────────────────────────────

@router.callback_query(CatalogBackCallback.filter())
async def back_to_categories(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        repo = ServiceCategoryRepository(session)
        categories = await repo.get_active_categories()

    if not categories:
        await callback.answer(CATALOG_EMPTY, show_alert=True)
        return

    await callback.message.edit_text(
        "Оберіть категорію послуг:",
        reply_markup=categories_keyboard(categories),
    )
    await callback.answer()


# ─── Вибір послуги → деталі ───────────────────────────────────────────────────

@router.callback_query(ServiceCallback.filter())
async def show_service_detail(callback: CallbackQuery, callback_data: ServiceCallback) -> None:
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        service = await repo.get_service_by_id(callback_data.service_id)

    if service is None:
        await callback.answer(SERVICE_NOT_FOUND, show_alert=True)
        return

    if service.price_max:
        price_text = f"від {int(service.price)} до {int(service.price_max)} грн"
    else:
        price_text = f"{int(service.price)} грн"

    text = (
        f"<b>{service.name}</b>\n\n"
        + (f"{service.description}\n\n" if service.description else "")
        + f"💰 Ціна: {price_text}\n"
        f"⏱ Тривалість: {service.duration_minutes} хв"
    )

    keyboard = service_detail_keyboard(service.id, service.category_id)

    if service.photo_file_id:
        await callback.message.answer_photo(
            photo=service.photo_file_id,
            caption=text,
            reply_markup=keyboard,
        )
        # видаляємо попереднє повідомлення зі списком
        await callback.message.delete()
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)

    await callback.answer()
