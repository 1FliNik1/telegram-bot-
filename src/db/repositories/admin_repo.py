from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.db.models.booking import Booking, BookingStatus
from src.db.models.master import Master, MasterService
from src.db.models.service import Service, ServiceCategory
from src.db.models.timeslot import TimeSlot
from src.db.repositories.base import BaseRepository

# ─── Service admin ────────────────────────────────────────────────────────────

class AdminServiceRepository(BaseRepository[Service]):
    model = Service

    async def get_all_services_with_categories(self) -> list[Service]:
        stmt = (
            select(Service)
            .options(joinedload(Service.category))
            .order_by(Service.category_id, Service.sort_order, Service.name)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_all_categories(self) -> list[ServiceCategory]:
        stmt = select(ServiceCategory).order_by(ServiceCategory.sort_order, ServiceCategory.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_service(
        self,
        category_id: int,
        name: str,
        price: Decimal,
        duration_minutes: int,
        price_max: Decimal | None = None,
        description: str | None = None,
        photo_file_id: str | None = None,
    ) -> Service:
        svc = Service(
            category_id=category_id,
            name=name,
            price=price,
            duration_minutes=duration_minutes,
            price_max=price_max,
            description=description,
            photo_file_id=photo_file_id,
            is_active=True,
        )
        self.session.add(svc)
        await self.session.flush()
        return svc

    async def toggle_active(self, service_id: int) -> bool | None:
        svc = await self.session.get(Service, service_id)
        if svc is None:
            return None
        svc.is_active = not svc.is_active
        return svc.is_active

    async def update_service(self, service_id: int, **fields) -> Service | None:
        svc = await self.session.get(Service, service_id)
        if svc is None:
            return None
        for k, v in fields.items():
            setattr(svc, k, v)
        return svc


# ─── Master admin ─────────────────────────────────────────────────────────────

class AdminMasterRepository(BaseRepository[Master]):
    model = Master

    async def get_all_masters(self) -> list[Master]:
        stmt = select(Master).order_by(Master.sort_order, Master.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_master(
        self,
        name: str,
        specialization: str | None = None,
        bio: str | None = None,
        photo_file_id: str | None = None,
    ) -> Master:
        master = Master(
            name=name,
            specialization=specialization,
            bio=bio,
            photo_file_id=photo_file_id,
            is_active=True,
        )
        self.session.add(master)
        await self.session.flush()
        return master

    async def toggle_active(self, master_id: int) -> bool | None:
        master = await self.session.get(Master, master_id)
        if master is None:
            return None
        master.is_active = not master.is_active
        return master.is_active

    async def link_service(self, master_id: int, service_id: int) -> None:
        """Link a service to a master (idempotent)."""
        existing = await self.session.execute(
            select(MasterService)
            .where(MasterService.master_id == master_id)
            .where(MasterService.service_id == service_id)
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(MasterService(master_id=master_id, service_id=service_id))

    async def get_master_services(self, master_id: int) -> list[Service]:
        stmt = (
            select(Service)
            .join(MasterService, MasterService.service_id == Service.id)
            .where(MasterService.master_id == master_id)
            .order_by(Service.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ─── Slot admin ───────────────────────────────────────────────────────────────

class AdminSlotRepository(BaseRepository[TimeSlot]):
    model = TimeSlot

    async def create_slots_for_day(
        self,
        master_id: int,
        target_date: date,
        work_start: time,
        work_end: time,
        slot_duration_minutes: int = 60,
    ) -> int:
        """Generate hourly slots for a day; skip if slot already exists. Returns count added."""
        added = 0
        current = _time_to_minutes(work_start)
        end_minutes = _time_to_minutes(work_end)

        while current + slot_duration_minutes <= end_minutes:
            start_t = _minutes_to_time(current)
            end_t = _minutes_to_time(current + slot_duration_minutes)

            # Check not already exists
            exists = await self.session.execute(
                select(TimeSlot)
                .where(TimeSlot.master_id == master_id)
                .where(TimeSlot.date == target_date)
                .where(TimeSlot.start_time == start_t)
            )
            if exists.scalar_one_or_none() is None:
                self.session.add(TimeSlot(
                    master_id=master_id,
                    date=target_date,
                    start_time=start_t,
                    end_time=end_t,
                    is_available=True,
                ))
                added += 1
            current += slot_duration_minutes

        return added

    async def get_slots_for_day(self, master_id: int, target_date: date) -> list[TimeSlot]:
        stmt = (
            select(TimeSlot)
            .where(TimeSlot.master_id == master_id)
            .where(TimeSlot.date == target_date)
            .order_by(TimeSlot.start_time)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_day_slots(self, master_id: int, target_date: date) -> int:
        """Delete only available (not booked) slots for a day."""
        slots = await self.get_slots_for_day(master_id, target_date)
        removed = 0
        for slot in slots:
            if slot.is_available:
                await self.session.delete(slot)
                removed += 1
        return removed


# ─── Booking admin ────────────────────────────────────────────────────────────

class AdminBookingRepository(BaseRepository[Booking]):
    model = Booking

    async def get_bookings_for_date(self, target_date: date) -> list[Booking]:
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.user),
                joinedload(Booking.service),
                joinedload(Booking.master),
                joinedload(Booking.timeslot),
            )
            .join(TimeSlot, TimeSlot.id == Booking.timeslot_id)
            .where(TimeSlot.date == target_date)
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]))
            .order_by(TimeSlot.start_time)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_bookings_by_master(self, master_id: int) -> list[Booking]:
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.user),
                joinedload(Booking.service),
                joinedload(Booking.timeslot),
            )
            .join(TimeSlot, TimeSlot.id == Booking.timeslot_id)
            .where(Booking.master_id == master_id)
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]))
            .where(TimeSlot.date >= date.today())
            .order_by(TimeSlot.date, TimeSlot.start_time)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _minutes_to_time(m: int) -> time:
    return time(m // 60, m % 60)
