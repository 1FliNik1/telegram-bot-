from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import distinct, select

from src.db.models.timeslot import TimeSlot
from src.db.repositories.base import BaseRepository

BOOKING_HORIZON_DAYS = 14


class TimeSlotRepository(BaseRepository[TimeSlot]):
    model = TimeSlot

    async def get_available_dates(
        self, master_ids: list[int], min_duration_minutes: int
    ) -> list[date]:
        """Dates in next 14 days where at least one slot fits the service duration."""
        today = date.today()
        max_date = today + timedelta(days=BOOKING_HORIZON_DAYS)

        stmt = (
            select(distinct(TimeSlot.date))
            .where(TimeSlot.master_id.in_(master_ids))
            .where(TimeSlot.is_available.is_(True))
            .where(TimeSlot.date >= today)
            .where(TimeSlot.date <= max_date)
            .order_by(TimeSlot.date)
        )
        result = await self.session.execute(stmt)
        all_dates = list(result.scalars().all())

        # Filter: only dates where at least one slot is long enough
        valid_dates: list[date] = []
        for d in all_dates:
            slots = await self.get_available_slots(master_ids, d)
            if any(_slot_duration_minutes(s) >= min_duration_minutes for s in slots):
                valid_dates.append(d)
        return valid_dates

    async def get_available_slots(
        self, master_ids: list[int], target_date: date
    ) -> list[TimeSlot]:
        """Available timeslots for given master(s) and date, ordered by start_time."""
        stmt = (
            select(TimeSlot)
            .where(TimeSlot.master_id.in_(master_ids))
            .where(TimeSlot.date == target_date)
            .where(TimeSlot.is_available.is_(True))
            .order_by(TimeSlot.start_time)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_booking(self, timeslot_id: int) -> TimeSlot | None:
        """Fetch slot only if still available — used inside a transaction."""
        stmt = (
            select(TimeSlot)
            .where(TimeSlot.id == timeslot_id)
            .where(TimeSlot.is_available.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


def _slot_duration_minutes(slot: TimeSlot) -> int:
    start = slot.start_time.hour * 60 + slot.start_time.minute
    end = slot.end_time.hour * 60 + slot.end_time.minute
    return end - start
