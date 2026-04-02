from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import IntegrityError

from src.db.base import async_session_factory
from src.db.models.booking import Booking
from src.db.repositories.booking_repo import BookingRepository
from src.db.repositories.timeslot_repo import TimeSlotRepository
from src.db.repositories.user_repo import UserRepository

if TYPE_CHECKING:
    from aiogram.types import User as TgUser


class SlotAlreadyTaken(Exception):
    """Raised when the chosen timeslot was taken by another user."""


async def confirm_booking(tg_user: TgUser, fsm_data: dict[str, Any]) -> Booking:
    """
    Atomically create a booking:
      1. Upsert the Telegram user in our DB.
      2. Re-check that the timeslot is still available (race condition guard).
      3. Mark slot as unavailable.
      4. Insert Booking record.

    SQLite serialises writes inside a transaction, so checking + marking
    in the same `session.begin()` block is sufficient for single-instance bots.
    The UNIQUE constraint on timeslot_id in bookings is a second DB-level guard.
    """
    timeslot_id: int = fsm_data["timeslot_id"]
    service_id: int = fsm_data["service_id"]
    master_id: int = fsm_data["actual_master_id"]

    async with async_session_factory() as session, session.begin():
        # 1. Upsert user
        user_repo = UserRepository(session)
        user = await user_repo.upsert(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name,
            username=tg_user.username,
            last_name=tg_user.last_name,
        )

        # 2. Check slot is still free (race condition guard)
        slot_repo = TimeSlotRepository(session)
        slot = await slot_repo.get_for_booking(timeslot_id)
        if slot is None:
            raise SlotAlreadyTaken()

        # 3. Mark slot as taken
        slot.is_available = False

        # 4. Create booking
        booking_repo = BookingRepository(session)
        try:
            booking = await booking_repo.create_booking(
                user_id=user.id,
                service_id=service_id,
                master_id=master_id,
                timeslot_id=timeslot_id,
            )
        except IntegrityError as err:
            # UNIQUE constraint on timeslot_id fired — another request
            # snuck in between our check and insert.
            raise SlotAlreadyTaken() from err

    return booking
