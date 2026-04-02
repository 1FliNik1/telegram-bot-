from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.filters.admin import IsAdmin
from src.bot.handlers.start import MAIN_MENU
from src.bot.keyboards.admin_kb import ADMIN_MENU
from src.db.base import async_session_factory
from src.db.repositories.admin_repo import AdminBookingRepository

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_STATUS_EMOJI = {
    "confirmed": "✅",
    "pending": "⏳",
    "cancelled": "❌",
    "completed": "💅",
    "no_show": "🚫",
}


def _fmt_bookings(bookings, title: str) -> str:
    if not bookings:
        return f"{title}\n\n📭 Записів немає."
    lines = [f"{title}\n"]
    for b in bookings:
        st = _STATUS_EMOJI.get(b.status.value, "❓")
        t = b.timeslot
        time_str = f"{t.start_time.hour:02d}:{t.start_time.minute:02d}"
        client = b.user.first_name if b.user else "?"
        lines.append(
            f"{st} {time_str} — {b.service.name}\n"
            f"   👩 {b.master.name}  |  👤 {client}"
        )
    return "\n".join(lines)


# ─── /admin ────────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🔐 <b>Адмін-панель</b>\n\nОберіть дію:",
        reply_markup=ADMIN_MENU,
    )


# ─── Bookings today / tomorrow ─────────────────────────────────────────────────

@router.message(F.text == "📅 Записи сьогодні")
async def admin_bookings_today(message: Message) -> None:
    today = date.today()
    async with async_session_factory() as session:
        repo = AdminBookingRepository(session)
        bookings = await repo.get_bookings_for_date(today)
    await message.answer(
        _fmt_bookings(bookings, f"📅 <b>Записи сьогодні ({today.strftime('%d.%m.%Y')})</b>")
    )


@router.message(F.text == "📅 Записи завтра")
async def admin_bookings_tomorrow(message: Message) -> None:
    tomorrow = date.today()
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    async with async_session_factory() as session:
        repo = AdminBookingRepository(session)
        bookings = await repo.get_bookings_for_date(tomorrow)
    await message.answer(
        _fmt_bookings(bookings, f"📅 <b>Записи завтра ({tomorrow.strftime('%d.%m.%Y')})</b>")
    )


# ─── Back to main menu ─────────────────────────────────────────────────────────

@router.message(F.text == "🏠 Головне меню")
async def admin_back_to_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Головне меню:", reply_markup=MAIN_MENU)
