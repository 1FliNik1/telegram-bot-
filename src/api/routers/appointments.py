from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_user, get_session
from src.api.schemas.appointment import (
    AppointmentOut,
    AppointmentsResponse,
    CancelResponse,
)
from src.db.models.booking import BookingStatus
from src.db.models.user import User
from src.db.repositories.booking_repo import BookingRepository

router = APIRouter()

CANCEL_THRESHOLD_SECONDS = 2 * 3600


@router.get("", response_model=AppointmentsResponse)
async def list_appointments(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
) -> AppointmentsResponse:
    repo = BookingRepository(session)
    bookings = await repo.get_user_upcoming_bookings(user.id)
    bookings.sort(key=lambda b: (b.timeslot.date, b.timeslot.start_time))
    items = [
        AppointmentOut(
            id=b.id,
            service_name=b.service.name,
            master_name=b.master.name,
            master_photo_file_id=b.master.photo_file_id,
            date=b.timeslot.date,
            start_time=b.timeslot.start_time,
            end_time=b.timeslot.end_time,
            price=float(b.service.price),
            status=b.status.value,
        )
        for b in bookings
    ]
    return AppointmentsResponse(appointments=items)


@router.post("/{booking_id}/cancel", response_model=CancelResponse)
async def cancel_appointment(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
) -> CancelResponse:
    repo = BookingRepository(session)
    booking = await repo.get_booking_by_id_for_user(booking_id, user.id)

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "already_cancelled"},
        )

    # 2-hour cancellation threshold
    slot_dt = datetime.combine(booking.timeslot.date, booking.timeslot.start_time)
    if (slot_dt - datetime.now()).total_seconds() < CANCEL_THRESHOLD_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "too_late_to_cancel"},
        )

    async with session.begin():
        await repo.cancel_booking(booking_id, user.id)

    return CancelResponse(status="cancelled", message="Запис скасовано")
