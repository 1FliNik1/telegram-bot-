import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot.handlers.about import router as about_router
from src.bot.handlers.admin import router as admin_router
from src.bot.handlers.admin_masters import router as admin_masters_router
from src.bot.handlers.admin_services import router as admin_services_router
from src.bot.handlers.admin_slots import router as admin_slots_router
from src.bot.handlers.booking import router as booking_router
from src.bot.handlers.catalog import router as catalog_router
from src.bot.handlers.my_bookings import router as my_bookings_router
from src.bot.handlers.notifications import router as notifications_router
from src.bot.handlers.price import router as price_router
from src.bot.handlers.start import router as start_router
from src.bot.middlewares.error_handler import error_router
from src.bot.middlewares.throttling import ThrottlingMiddleware
from src.config import settings
from src.services.notification_service import (
    send_2h_reminders,
    send_24h_reminders,
    send_review_requests,
)

logger = logging.getLogger(__name__)


def _setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    # Check every 15 minutes — wide enough to catch all bookings in the window
    scheduler.add_job(
        send_24h_reminders, "interval", minutes=15,
        kwargs={"bot": bot},
        id="reminder_24h",
    )
    scheduler.add_job(
        send_2h_reminders, "interval", minutes=15,
        kwargs={"bot": bot},
        id="reminder_2h",
    )
    scheduler.add_job(
        send_review_requests, "interval", minutes=30,
        kwargs={"bot": bot},
        id="review_request",
    )
    return scheduler


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(ThrottlingMiddleware())

    # Error handler (must be first router)
    dp.include_router(error_router)

    # Admin routers first — they have IsAdmin filter so non-admins pass through
    dp.include_router(admin_router)
    dp.include_router(admin_services_router)
    dp.include_router(admin_masters_router)
    dp.include_router(admin_slots_router)
    # User routers
    dp.include_router(booking_router)       # before catalog — FSM state filters take priority
    dp.include_router(my_bookings_router)
    dp.include_router(notifications_router)
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(price_router)
    dp.include_router(about_router)

    scheduler = _setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started — 24h/2h reminders and review requests active.")

    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(main())
