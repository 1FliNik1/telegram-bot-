from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.keyboards.booking_kb import BookStartCallback  # noqa: F401 re-exported
from src.db.models.service import Service, ServiceCategory


class CategoryCallback(CallbackData, prefix="cat"):
    category_id: int


class ServiceCallback(CallbackData, prefix="svc"):
    service_id: int


class CatalogBackCallback(CallbackData, prefix="cat_back"):
    """Повернення до списку категорій."""
    pass


def categories_keyboard(categories: list[ServiceCategory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        label = f"{cat.emoji} {cat.name}" if cat.emoji else cat.name
        builder.button(
            text=label,
            callback_data=CategoryCallback(category_id=cat.id),
        )
    builder.adjust(1)
    return builder.as_markup()


def services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        if svc.price_max:
            price_label = f"від {int(svc.price)}–{int(svc.price_max)} грн"
        else:
            price_label = f"{int(svc.price)} грн"
        builder.button(
            text=f"{svc.name} · {price_label} · {svc.duration_minutes} хв",
            callback_data=ServiceCallback(service_id=svc.id),
        )
    builder.button(text="← Назад", callback_data=CatalogBackCallback())
    builder.adjust(1)
    return builder.as_markup()


def service_detail_keyboard(service_id: int, category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✂️ Записатись", callback_data=BookStartCallback(service_id=service_id))
    builder.button(
        text="← Назад до послуг",
        callback_data=CategoryCallback(category_id=category_id),
    )
    builder.adjust(1)
    return builder.as_markup()
