from __future__ import annotations

from datetime import date, time
from typing import List

from pydantic import BaseModel


class AvailableDateOut(BaseModel):
    date: date
    day_name: str


class AvailableDatesResponse(BaseModel):
    dates: List[AvailableDateOut]


class SlotOut(BaseModel):
    id: int
    start_time: time
    end_time: time
    master_id: int


class AvailableSlotsResponse(BaseModel):
    date: date
    slots: List[SlotOut]


class BookingCreateIn(BaseModel):
    service_id: int
    master_id: int
    timeslot_id: int


class BookingOut(BaseModel):
    id: int
    service_name: str
    master_name: str
    date: date
    start_time: time
    end_time: time
    status: str


class BookingCreateResponse(BaseModel):
    appointment: BookingOut
