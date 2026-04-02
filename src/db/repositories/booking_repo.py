from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.db.models.booking import Booking, BookingStatus
from src.db.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    async def create_booking(
        self,
        user_id: int,
        service_id: int,
        master_id: int,
        timeslot_id: int,
    ) -> Booking:
        booking = Booking(
            user_id=user_id,
            service_id=service_id,
            master_id=master_id,
            timeslot_id=timeslot_id,
            status=BookingStatus.CONFIRMED,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def get_user_upcoming_bookings(self, user_id: int) -> list[Booking]:
        """Active (confirmed/pending) bookings for a user, with related data loaded."""
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.service),
                joinedload(Booking.master),
                joinedload(Booking.timeslot),
            )
            .where(Booking.user_id == user_id)
            .where(
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            )
            .order_by(Booking.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_booking_by_id_for_user(
        self, booking_id: int, user_id: int
    ) -> Optional[Booking]:
        """Fetch a single booking with all related data, scoped to a specific user."""
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.service),
                joinedload(Booking.master),
                joinedload(Booking.timeslot),
            )
            .where(Booking.id == booking_id)
            .where(Booking.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def cancel_booking(self, booking_id: int, user_id: int) -> bool:
        """Cancel booking by id; returns False if not found or already cancelled."""
        stmt = (
            select(Booking)
            .options(joinedload(Booking.timeslot))
            .where(Booking.id == booking_id)
            .where(Booking.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        booking = result.scalar_one_or_none()

        if booking is None or booking.status == BookingStatus.CANCELLED:
            return False

        booking.status = BookingStatus.CANCELLED
        # Free the timeslot so others can book it
        if booking.timeslot is not None:
            booking.timeslot.is_available = True
        return True
