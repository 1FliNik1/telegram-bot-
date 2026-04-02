from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_user, get_session
from src.api.schemas.booking import (
    AvailableDateOut,
    AvailableDatesResponse,
    AvailableSlotsResponse,
    BookingCreateIn,
    BookingCreateResponse,
    BookingOut,
    SlotOut,
)
from src.db.base import async_session_factory
from src.db.models.user import User
from src.db.repositories.booking_repo import BookingRepository
from src.db.repositories.master_repo import MasterRepository
from src.db.repositories.service_repo import ServiceRepository
from src.db.repositories.timeslot_repo import TimeSlotRepository, _slot_duration_minutes

router = APIRouter()

_DAY_NAMES_UK = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Нд"}


@router.get("/available-dates", response_model=AvailableDatesResponse)
async def available_dates(
    service_id: int = Query(...),
    master_id: Optional[int] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> AvailableDatesResponse:
    svc_repo = ServiceRepository(session)
    master_repo = MasterRepository(session)
    slot_repo = TimeSlotRepository(session)

    svc = await svc_repo.get_service_by_id(service_id)
    if svc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    if master_id is not None:
        master_ids = [master_id]
    else:
        masters = await master_repo.get_masters_by_service(service_id)
        master_ids = [m.id for m in masters]

    if not master_ids:
        return AvailableDatesResponse(dates=[])

    dates = await slot_repo.get_available_dates(master_ids, svc.duration_minutes)
    return AvailableDatesResponse(
        dates=[
            AvailableDateOut(date=d, day_name=_DAY_NAMES_UK[d.weekday()])
            for d in dates
        ]
    )


@router.get("/available-slots", response_model=AvailableSlotsResponse)
async def available_slots(
    service_id: int = Query(...),
    master_id: int = Query(...),
    target_date: date = Query(..., alias="date"),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_db_user),
) -> AvailableSlotsResponse:
    svc_repo = ServiceRepository(session)
    slot_repo = TimeSlotRepository(session)

    if target_date < date.today():
        return AvailableSlotsResponse(date=target_date, slots=[])

    svc = await svc_repo.get_service_by_id(service_id)
    if svc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    slots = await slot_repo.get_available_slots([master_id], target_date)
    slot_items = [
        SlotOut(
            id=s.id,
            start_time=s.start_time,
            end_time=s.end_time,
            master_id=s.master_id,
        )
        for s in slots
        if _slot_duration_minutes(s) >= svc.duration_minutes
    ]
    return AvailableSlotsResponse(date=target_date, slots=slot_items)


@router.post("/create", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    body: BookingCreateIn,
    user: User = Depends(get_db_user),
) -> BookingCreateResponse:
    """Create a booking with race condition guard."""
    async with async_session_factory() as session, session.begin():
        slot_repo = TimeSlotRepository(session)
        slot = await slot_repo.get_for_booking(body.timeslot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "slot_taken"},
            )
        slot.is_available = False

        booking_repo = BookingRepository(session)
        try:
            booking = await booking_repo.create_booking(
                user_id=user.id,
                service_id=body.service_id,
                master_id=body.master_id,
                timeslot_id=body.timeslot_id,
            )
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "slot_taken"},
            ) from exc

        # Capture fields before session closes
        booking_id = booking.id
        slot_date = slot.date
        slot_start = slot.start_time
        slot_end = slot.end_time

    # Re-fetch with relations in a new session to build response
    async with async_session_factory() as session2:
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        from src.db.models.booking import Booking

        stmt = (
            select(Booking)
            .options(joinedload(Booking.service), joinedload(Booking.master))
            .where(Booking.id == booking_id)
        )
        result = await session2.execute(stmt)
        b = result.unique().scalar_one()
        return BookingCreateResponse(
            appointment=BookingOut(
                id=b.id,
                service_name=b.service.name,
                master_name=b.master.name,
                date=slot_date,
                start_time=slot_start,
                end_time=slot_end,
                status=b.status.value,
            )
        )
