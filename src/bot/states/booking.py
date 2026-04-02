from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class BookingState(StatesGroup):
    select_service = State()   # category → service selection
    select_master = State()    # master selection
    select_date = State()      # date selection
    select_time = State()      # timeslot selection
    confirm = State()          # confirmation screen
