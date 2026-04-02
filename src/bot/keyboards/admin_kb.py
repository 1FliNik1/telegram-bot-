from __future__ import annotations

from datetime import date, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.db.models.master import Master
from src.db.models.service import Service, ServiceCategory

# ─── Callback data ────────────────────────────────────────────────────────────

class AdminActionCallback(CallbackData, prefix="adm"):
    action: str  # services | masters | slots | bookings_today | bookings_tomorrow | bookings_master

class AdminServiceCallback(CallbackData, prefix="adm_svc"):
    service_id: int

class AdminServiceToggleCallback(CallbackData, prefix="adm_svc_tog"):
    service_id: int

class AdminCategoryCallback(CallbackData, prefix="adm_cat"):
    category_id: int

class AdminMasterCallback(CallbackData, prefix="adm_mst"):
    master_id: int

class AdminMasterToggleCallback(CallbackData, prefix="adm_mst_tog"):
    master_id: int

class AdminSlotDateCallback(CallbackData, prefix="adm_slot_d"):
    date_str: str   # YYYY-MM-DD
    master_id: int

class AdminSlotHourCallback(CallbackData, prefix="adm_slot_h"):
    hour: int       # 8-20

class AdminConfirmCallback(CallbackData, prefix="adm_ok"):
    pass

class AdminCancelCallback(CallbackData, prefix="adm_x"):
    pass

class AdminSkipCallback(CallbackData, prefix="adm_skip"):
    pass

# ─── Keyboards ────────────────────────────────────────────────────────────────

ADMIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛠 Послуги"), KeyboardButton(text="👤 Майстри")],
        [KeyboardButton(text="📅 Записи сьогодні"), KeyboardButton(text="📅 Записи завтра")],
        [KeyboardButton(text="⏰ Слоти"), KeyboardButton(text="🏠 Головне меню")],
    ],
    resize_keyboard=True,
)


def _cancel_row(builder: InlineKeyboardBuilder) -> None:
    builder.button(text="❌ Скасувати", callback_data=AdminCancelCallback())


def _skip_row(builder: InlineKeyboardBuilder, label: str = "⏩ Пропустити") -> None:
    builder.button(text=label, callback_data=AdminSkipCallback())


# Services list

def admin_services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        status = "✅" if svc.is_active else "❌"
        builder.button(
            text=f"{status} {svc.name} — {int(svc.price)} грн",
            callback_data=AdminServiceCallback(service_id=svc.id),
        )
    builder.button(text="➕ Додати послугу", callback_data=AdminActionCallback(action="add_service"))
    _cancel_row(builder)
    builder.adjust(1)
    return builder.as_markup()


def admin_service_detail_keyboard(service_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_label = "🔴 Деактивувати" if is_active else "🟢 Активувати"
    builder.button(text=toggle_label, callback_data=AdminServiceToggleCallback(service_id=service_id))
    builder.button(text="← Назад", callback_data=AdminActionCallback(action="services"))
    builder.adjust(2)
    return builder.as_markup()


def admin_categories_keyboard(categories: list[ServiceCategory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        label = f"{cat.emoji} {cat.name}" if cat.emoji else cat.name
        builder.button(text=label, callback_data=AdminCategoryCallback(category_id=cat.id))
    _cancel_row(builder)
    builder.adjust(1)
    return builder.as_markup()


# Masters list

def admin_masters_keyboard(masters: list[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in masters:
        status = "✅" if m.is_active else "❌"
        builder.button(
            text=f"{status} {m.name}",
            callback_data=AdminMasterCallback(master_id=m.id),
        )
    builder.button(text="➕ Додати майстра", callback_data=AdminActionCallback(action="add_master"))
    _cancel_row(builder)
    builder.adjust(1)
    return builder.as_markup()


def admin_master_detail_keyboard(master_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_label = "🔴 Деактивувати" if is_active else "🟢 Активувати"
    builder.button(text=toggle_label, callback_data=AdminMasterToggleCallback(master_id=master_id))
    builder.button(text="⏰ Слоти майстра", callback_data=AdminActionCallback(action=f"slots_master_{master_id}"))
    builder.button(text="← Назад", callback_data=AdminActionCallback(action="masters"))
    builder.adjust(2)
    return builder.as_markup()


# Slot management — master selection

def admin_slot_masters_keyboard(masters: list[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in masters:
        builder.button(text=f"👤 {m.name}", callback_data=AdminMasterCallback(master_id=m.id))
    _cancel_row(builder)
    builder.adjust(1)
    return builder.as_markup()


# Slot management — date selection (next 14 days)

def admin_slot_dates_keyboard(master_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = date.today()
    _DAYS_UA = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    for i in range(14):
        d = today + timedelta(days=i)
        label = f"{_DAYS_UA[d.weekday()]} {d.day:02d}.{d.month:02d}"
        builder.button(
            text=label,
            callback_data=AdminSlotDateCallback(date_str=d.isoformat(), master_id=master_id),
        )
    _cancel_row(builder)
    builder.adjust(4)
    return builder.as_markup()


# Slot management — hours multi-select (stored as comma-sep string in FSM)

def admin_hours_keyboard(selected_hours: set[int]) -> InlineKeyboardMarkup:
    """9:00–19:00, each button toggles selected state."""
    builder = InlineKeyboardBuilder()
    for h in range(9, 20):
        mark = "✅" if h in selected_hours else ""
        builder.button(
            text=f"{mark} {h:02d}:00",
            callback_data=AdminSlotHourCallback(hour=h),
        )
    builder.button(text="✅ Зберегти", callback_data=AdminConfirmCallback())
    _cancel_row(builder)
    builder.adjust(4)
    return builder.as_markup()


# Confirm / cancel

def admin_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Підтвердити", callback_data=AdminConfirmCallback())
    _cancel_row(builder)
    builder.adjust(2)
    return builder.as_markup()


def admin_skip_keyboard(skip_label: str = "⏩ Пропустити") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _skip_row(builder, skip_label)
    _cancel_row(builder)
    builder.adjust(2)
    return builder.as_markup()
