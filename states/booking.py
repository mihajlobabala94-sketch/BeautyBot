from aiogram.fsm.state import State, StatesGroup


class BookingState(StatesGroup):
    name = State()
    previous_brows = State()
    brow_photo = State()
    phone = State()
    service = State()
    date = State()
    time = State()