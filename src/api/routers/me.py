from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_user, get_session
from src.api.schemas.user import MeResponse, UpcomingAppointmentOut
from src.db.models.booking import Booking, BookingStatus
from src.db.models.user import User
from src.db.repositories.booking_repo import BookingRepository

router = APIRouter()


@router.get("/me", response_model=MeResponse)
async def get_me(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
) -> MeResponse:
    repo = BookingRepository(session)

    # Total completed visits
    count_stmt = (
        select(func.count())
        .select_from(Booking)
        .where(Booking.user_id == user.id)
        .where(Booking.status == BookingStatus.COMPLETED)
    )
    total_visits: int = (await session.execute(count_stmt)).scalar_one()

    # Upcoming appointment (soonest)
    upcoming_bookings = await repo.get_user_upcoming_bookings(user.id)
    upcoming_bookings.sort(key=lambda b: (b.timeslot.date, b.timeslot.start_time))

    upcoming = None
    if upcoming_bookings:
        b = upcoming_bookings[0]
        upcoming = UpcomingAppointmentOut(
            id=b.id,
            service_name=b.service.name,
            master_name=b.master.name,
            date=b.timeslot.date,
            start_time=b.timeslot.start_time,
            end_time=b.timeslot.end_time,
        )

    return MeResponse(
        first_name=user.first_name,
        total_visits=total_visits,
        upcoming_appointment=upcoming,
    )
