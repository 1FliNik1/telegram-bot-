from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import settings

router = Router(name="about")


def _about_keyboard() -> InlineKeyboardMarkup | None:
    if not settings.salon_maps_url:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Відкрити на карті", url=settings.salon_maps_url)
    return builder.as_markup()


def _about_text() -> str:
    return (
        f"ℹ️ <b>{settings.salon_name}</b>\n\n"
        f"📍 <b>Адреса:</b> {settings.salon_address}\n"
        f"📞 <b>Телефон:</b> {settings.salon_phone}\n"
        f"🕐 <b>Графік роботи:</b>\n{settings.salon_schedule}\n\n"
        "Записатись онлайн можна прямо тут у боті — натисніть <b>📅 Записатись</b>."
    )


@router.message(Command("about"))
@router.message(F.text == "ℹ️ Про салон")
async def cmd_about(message: Message) -> None:
    text = _about_text()
    keyboard = _about_keyboard()

    if settings.salon_photo_file_id:
        await message.answer_photo(
            photo=settings.salon_photo_file_id,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await message.answer(text, reply_markup=keyboard)
