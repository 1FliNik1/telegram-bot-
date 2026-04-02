from __future__ import annotations

from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class UpcomingAppointmentOut(BaseModel):
    id: int
    service_name: str
    master_name: str
    date: date
    start_time: time
    end_time: time


class MeResponse(BaseModel):
    first_name: str
    total_visits: int
    upcoming_appointment: Optional[UpcomingAppointmentOut]
