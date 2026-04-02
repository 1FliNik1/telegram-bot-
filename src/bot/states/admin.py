from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminServiceState(StatesGroup):
    """FSM for adding / editing a service."""
    choose_action = State()      # add or edit
    choose_category = State()
    enter_name = State()
    enter_price = State()
    enter_price_max = State()
    enter_duration = State()
    enter_description = State()
    upload_photo = State()
    confirm = State()


class AdminMasterState(StatesGroup):
    """FSM for adding / editing a master."""
    choose_action = State()
    enter_name = State()
    enter_specialization = State()
    enter_bio = State()
    upload_photo = State()
    confirm = State()


class AdminSlotState(StatesGroup):
    """FSM for managing timeslots."""
    choose_master = State()
    choose_date = State()
    choose_hours = State()
    confirm = State()
