from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards.price_kb import price_category_keyboard
from src.db.base import async_session_factory
from src.db.models.service import Service, ServiceCategory
from src.db.repositories.service_repo import (
    ServiceCategoryRepository,
    ServiceRepository,
)

router = Router(name="price")

PRICE_EMPTY = "На жаль, прайс-лист порожній. Спробуйте пізніше."
PRICE_HEADER = "💰 <b>Прайс-лист</b>\n"


def _format_price(service: Service) -> str:
    if service.price_max:
        return f"від {int(service.price)}–{int(service.price_max)} грн"
    return f"{int(service.price)} грн"


def _build_category_block(category: ServiceCategory, services: list[Service]) -> str:
    """Формує текстовий блок однієї категорії у вигляді дерева."""
    label = f"{category.emoji} {category.name}" if category.emoji else category.name
    lines = [f"<b>{label}</b>"]

    for i, svc in enumerate(services):
        prefix = "└" if i == len(services) - 1 else "├"
        price = _format_price(svc)
        lines.append(f"{prefix} {svc.name} — {price} · {svc.duration_minutes} хв")

    return "\n".join(lines)


@router.message(Command("price"))
@router.message(F.text == "💰 Прайс-лист")
async def show_price(message: Message) -> None:
    async with async_session_factory() as session:
        cat_repo = ServiceCategoryRepository(session)
        svc_repo = ServiceRepository(session)

        categories = await cat_repo.get_active_categories()

        if not categories:
            await message.answer(PRICE_EMPTY)
            return

        # збираємо послуги для всіх категорій
        category_services: list[tuple[ServiceCategory, list[Service]]] = []
        for cat in categories:
            services = await svc_repo.get_services_by_category(cat.id)
            if services:
                category_services.append((cat, services))

    if not category_services:
        await message.answer(PRICE_EMPTY)
        return

    # перше повідомлення — заголовок
    await message.answer(PRICE_HEADER)

    # кожна категорія — окреме повідомлення з кнопкою "Записатись"
    for cat, services in category_services:
        text = _build_category_block(cat, services)
        await message.answer(
            text,
            reply_markup=price_category_keyboard(cat.id),
        )
