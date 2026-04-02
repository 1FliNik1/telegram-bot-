from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from src.config import settings
from src.db.base import async_session_factory
from src.db.repositories.user_repo import UserRepository

router = Router(name="start")

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Каталог послуг"), KeyboardButton(text="💰 Прайс-лист")],
        [KeyboardButton(text="📅 Записатись"), KeyboardButton(text="📖 Мої записи")],
        [KeyboardButton(text="ℹ️ Про салон")],
    ],
    resize_keyboard=True,
)


def _miniapp_keyboard() -> InlineKeyboardMarkup | None:
    if not settings.miniapp_url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💅 Відкрити додаток",
                    web_app=WebAppInfo(url=settings.miniapp_url),
                )
            ]
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Upsert user in DB on every /start
    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.upsert(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            last_name=message.from_user.last_name,
        )
        await session.commit()

    await message.answer(
        f"Привіт, {message.from_user.first_name}! 👋\n\n"
        "Ласкаво просимо до бота салону краси.\n"
        "Оберіть дію з меню нижче.",
        reply_markup=MAIN_MENU,
    )

    if kb := _miniapp_keyboard():
        await message.answer(
            "Або відкрийте повний додаток для запису 👇",
            reply_markup=kb,
        )
