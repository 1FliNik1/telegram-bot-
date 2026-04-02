from __future__ import annotations

from datetime import date

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.db.models.master import Master
from src.db.models.service import Service, ServiceCategory
from src.db.models.timeslot import TimeSlot

# ─── Ukrainian locale helpers ────────────────────────────────────────────────

_MONTHS_SHORT = [
    "", "Січ", "Лют", "Бер", "Кві", "Тра", "Чер",
    "Лип", "Сер", "Вер", "Жов", "Лис", "Гру",
]
_MONTHS_GEN = [
    "", "Січня", "Лютого", "Березня", "Квітня", "Травня", "Червня",
    "Липня", "Серпня", "Вересня", "Жовтня", "Листопада", "Грудня",
]
_DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
_DAYS_FULL = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]


def format_date_button(d: date) -> str:
    """'Пт 4 Кві' for inline button label."""
    day_name = _DAYS_SHORT[d.weekday()]
    return f"{day_name} {d.day} {_MONTHS_SHORT[d.month]}"


def format_date_long(d: date) -> str:
    """'4 Квітня (П'ятниця)' for message text."""
    return f"{d.day} {_MONTHS_GEN[d.month]} ({_DAYS_FULL[d.weekday()]})"


def format_time(t) -> str:
    return t.strftime("%H:%M")


# ─── Callback data classes ───────────────────────────────────────────────────

class BookStartCallback(CallbackData, prefix="book_start"):
    """Entry point from catalog service detail: skip to master selection."""
    service_id: int


class BookCategoryCallback(CallbackData, prefix="bk_cat"):
    category_id: int


class BookServiceCallback(CallbackData, prefix="bk_svc"):
    service_id: int


class BookBackToCatsCallback(CallbackData, prefix="bk_bcat"):
    """Back to category list inside booking flow."""
    pass


class MasterSelectCallback(CallbackData, prefix="bk_mst"):
    master_id: int  # 0 = any master


class DateSelectCallback(CallbackData, prefix="bk_date"):
    date_str: str   # "YYYY-MM-DD"


class SlotSelectCallback(CallbackData, prefix="bk_slot"):
    timeslot_id: int


class BookConfirmCallback(CallbackData, prefix="bk_ok"):
    pass


class BookCancelFlowCallback(CallbackData, prefix="bk_x"):
    pass


# ─── Keyboard builders ───────────────────────────────────────────────────────

def _cancel_button(builder: InlineKeyboardBuilder) -> None:
    builder.button(text="❌ Скасувати", callback_data=BookCancelFlowCallback())


def booking_categories_keyboard(categories: list[ServiceCategory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        label = f"{cat.emoji} {cat.name}" if cat.emoji else cat.name
        builder.button(text=label, callback_data=BookCategoryCallback(category_id=cat.id))
    _cancel_button(builder)
    builder.adjust(1)
    return builder.as_markup()


def booking_services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        if svc.price_max:
            price = f"від {int(svc.price)}–{int(svc.price_max)} грн"
        else:
            price = f"{int(svc.price)} грн"
        builder.button(
            text=f"{svc.name} · {price} · {svc.duration_minutes} хв",
            callback_data=BookServiceCallback(service_id=svc.id),
        )
    builder.button(text="← Назад", callback_data=BookBackToCatsCallback())
    _cancel_button(builder)
    builder.adjust(1)
    return builder.as_markup()


def masters_keyboard(masters: list[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for master in masters:
        spec = f" — {master.specialization}" if master.specialization else ""
        builder.button(
            text=f"👤 {master.name}{spec}",
            callback_data=MasterSelectCallback(master_id=master.id),
        )
    builder.button(text="🎲 Будь-який вільний", callback_data=MasterSelectCallback(master_id=0))
    _cancel_button(builder)
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard(dates: list[date]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in dates:
        builder.button(
            text=format_date_button(d),
            callback_data=DateSelectCallback(date_str=d.isoformat()),
        )
    _cancel_button(builder)
    builder.adjust(4)
    return builder.as_markup()


def timeslots_keyboard(slots: list[TimeSlot], min_duration: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        slot_dur = (slot.end_time.hour * 60 + slot.end_time.minute) - \
                   (slot.start_time.hour * 60 + slot.start_time.minute)
        if slot_dur < min_duration:
            continue
        label = f"{format_time(slot.start_time)} – {format_time(slot.end_time)}"
        builder.button(text=label, callback_data=SlotSelectCallback(timeslot_id=slot.id))
    _cancel_button(builder)
    builder.adjust(3)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Підтвердити", callback_data=BookConfirmCallback())
    builder.button(text="❌ Скасувати", callback_data=BookCancelFlowCallback())
    builder.adjust(2)
    return builder.as_markup()
