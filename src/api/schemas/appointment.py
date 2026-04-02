from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel


class AppointmentOut(BaseModel):
    id: int
    service_name: str
    master_name: str
    master_photo_file_id: Optional[str]
    date: date
    start_time: time
    end_time: time
    price: Optional[float]
    status: str


class AppointmentsResponse(BaseModel):
    appointments: List[AppointmentOut]


class CancelResponse(BaseModel):
    status: str
    message: str
